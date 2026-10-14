"""Build pinned Luanti Android native code with an isolated source-built SDL."""
from pathlib import Path
import hashlib
import os
import re
import shutil
import subprocess
import urllib.request
import zipfile
ROOT=Path(__file__).resolve().parents[1]
pins=[('luanti','luanti-org/luanti','5.17.0','c0e6812b1a4260bb25a1f606f70f55f4962bb97d'),('voxelibre','VoxeLibre/VoxeLibre','0.92.3','a523240fb89713ffa6302696e8275bbd7de3bd49'),('sdl-luanti','libsdl-org/SDL','release-2.32.10','5d249570393f7a37e037abf22cd6012a4cc56a71')]
for name,repo,tag,revision in pins:
    source=ROOT/'.sources'/name
    if not source.exists():subprocess.run(['git','clone','--depth','1','--branch',tag,'https://github.com/'+repo,str(source)],check=True)
    if subprocess.check_output(['git','-C',str(source),'rev-parse','HEAD'],text=True).strip()!=revision or subprocess.run(['git','-C',str(source),'diff','--quiet']).returncode:
        raise SystemExit('Preserve changed source; use pinned clean '+name+' '+revision)
work=ROOT/'build/luanti-source'
shutil.copytree(ROOT/'.sources/luanti',work,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.git','.gradle','.cxx','build','deps'))
archive=ROOT/'build/luanti-deps-lite.zip'
expected='7fd7221b2ca6abe44eb21cd287f49c008e367ad08bd43da73bb60df7df73ebfa'
if not archive.exists():
    archive.parent.mkdir(parents=True,exist_ok=True)
    urllib.request.urlretrieve('https://github.com/luanti-org/luanti_android_deps/releases/download/latest/deps-lite.zip',archive)
if hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()!=expected:
    raise SystemExit('Luanti dependency archive changed; preserve it and review rather than using an unpinned binary.')
deps=work/'android/native/deps';deps.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive) as z:
    # Keep the other directory marker so upstream skips its unpinned downloader.
    (deps/'armeabi-v7a').mkdir(exist_ok=True)
    for item in z.infolist():
        if item.filename.startswith('arm64-v8a/'):
            target=deps/item.filename
            if item.is_dir():target.mkdir(parents=True,exist_ok=True)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_bytes(z.read(item.filename))
sdl=ROOT/'build/luanti-sdl-source'
shutil.copytree(ROOT/'.sources/sdl-luanti',sdl,dirs_exist_ok=True,ignore=shutil.ignore_patterns('.git','build'))
for p in sdl.rglob('*'):
    if not p.is_file() or p.suffix not in ('.c','.cpp','.h','.java'):continue
    before=p.read_bytes()
    after=before.replace(b'org/libsdl/app',b'io/precisiondata/joyorbit/voxel/sdl').replace(b'org.libsdl.app',b'io.precisiondata.joyorbit.voxel.sdl').replace(b'org_libsdl_app',b'io_precisiondata_joyorbit_voxel_sdl')
    if before!=after:p.write_bytes(after)
ndk=Path(os.environ.get('JOYORBIT_NATIVE_NDK',str(Path(os.environ['ANDROID_SDK_ROOT'])/'ndk/29.0.14206865')))
sdl_build=ROOT/'build/luanti-sdl-build'
subprocess.run(['cmake','-S',str(sdl),'-B',str(sdl_build),'-G','Ninja','-DCMAKE_TOOLCHAIN_FILE='+str(ndk/'build/cmake/android.toolchain.cmake'),'-DANDROID_ABI=arm64-v8a','-DANDROID_PLATFORM=android-21','-DCMAKE_BUILD_TYPE=Release','-DSDL_SHARED=OFF','-DSDL_STATIC=ON','-DSDL_STATIC_PIC=ON','-DSDL_TEST=OFF','-DSDL2_DISABLE_SDL2MAIN=ON'],check=True)
subprocess.run(['cmake','--build',str(sdl_build),'-j','6'],check=True)
shutil.copy2(sdl_build/'libSDL2.a',deps/'arm64-v8a/SDL2/libSDL2.a')
# Upstream Android discards SDL arguments and always opens the engine menu.
# Preserve our fixed --go/private-world arguments instead.
p=work/'src/porting_android.cpp';text=p.read_text()
old='char *argv[] = {strdup(PROJECT_NAME), strdup("--verbose"), nullptr};\n\tint retval = main(ARRLEN(argv) - 1, argv);\n\tfree(argv[0]);\n\tfree(argv[1]);'
if old not in text:raise SystemExit('Pinned Luanti Android entry context changed')
text=text.replace(old,'int retval = main(_argc, _argv);',1);p.write_text(text)
# The library provides credits and settings; the native pause screen needs
# only resume, controls and a clean save/quit back to JoyOrbit.
p=work/'src/client/game_formspec.cpp';text=p.read_text()
a=text.index('void GameFormSpec::showPauseMenu()')
b=text.index('\n}',a)+2
text=text[:a]+'''void GameFormSpec::showPauseMenu()
{
    const std::string formspec =
        "formspec_version[6]size[10,7]"
        "label[1,0.7;VoxeLibre]"
        "button_exit[1,1.4;8,0.8;btn_continue;Resume]"
        "button_exit[1,2.5;8,0.8;btn_exit_os;Return to JoyOrbit]"
        "textarea[1,3.8;8,2.5;;Left stick or D-pad: move\\nRight stick: look\\nA: jump  Y: inventory\\nTriggers: dig and place\\nSelect + Start: save and return;]";
    FormspecFormSource *source = new FormspecFormSource(formspec);
    HardcodedPauseFormspecHandler *handler = new HardcodedPauseFormspecHandler();
    GUIFormSpecMenu::create(m_formspec, m_client, m_rendering_engine->get_gui_env(),
        source, handler, m_client->getFormspecPrepend(), m_client->getSoundManager());
    m_formspec->setFocus("btn_continue");
}'''+text[b:]
p.write_text(text)
android=work/'android'
(android/'settings.gradle').write_text('rootProject.name="JoyOrbit-Luanti-Native"\ninclude ":native"\n')
(android/'local.properties').write_text('sdk.dir='+os.environ['ANDROID_SDK_ROOT']+'\n')
p=android/'native/build.gradle';s=p.read_text().replace('"-DENABLE_CURL=1"','"-DENABLE_CURL=0"').replace("include 'armeabi-v7a', 'arm64-v8a', 'x86', 'x86_64'","include 'arm64-v8a'")
s=s.replace('defaultConfig {','defaultConfig {\n        ndk { abiFilters "arm64-v8a" }',1)
s=s.replace('compileSdk = 34','compileSdk = 36')
s=s.replace('buildTypes {','buildTypes {\n        debug { externalNativeBuild { cmake { arguments \"-DCMAKE_BUILD_TYPE=RelWithDebInfo\" } } }',1)
p.write_text(s)
subprocess.run(['sh',str(android/'gradlew'),'-p',str(android),':native:assembleDebug','--no-daemon'],check=True)
print('Luanti native AAR built. Java embedding, offline world preparation, controls and save acceptance remain required.')
