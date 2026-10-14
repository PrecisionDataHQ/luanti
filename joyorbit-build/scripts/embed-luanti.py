"""Embed source-built Luanti/VoxeLibre with a fixed offline-world launcher."""
from pathlib import Path
import os
import re
import shutil
import subprocess
import zipfile
ROOT=Path(__file__).resolve().parents[1]
work=ROOT/'build/luanti-source'
native=work/'android/native/build/outputs/aar/native-debug.aar'
if not native.is_file():raise SystemExit('Build pinned source with prepare-luanti.py first.')
module=ROOT/'build/luanti-embedded';module.mkdir(parents=True,exist_ok=True)
java=module/'java';java.mkdir(parents=True,exist_ok=True)
upstream=work/'android/app/src/main/java'
shutil.copytree(upstream/'org/libsdl/app',java/'io/precisiondata/joyorbit/voxel/sdl',dirs_exist_ok=True)
for p in (java/'io/precisiondata/joyorbit/voxel/sdl').rglob('*.java'):
    p.write_text(p.read_text().replace('org.libsdl.app','io.precisiondata.joyorbit.voxel.sdl'))
parent=java/'net/minetest/minetest';parent.mkdir(parents=True,exist_ok=True)
for name in ('GameActivity.java','CustomEditText.java','Utils.java'):
    s=(upstream/'net/minetest/minetest'/name).read_text().replace('org.libsdl.app','io.precisiondata.joyorbit.voxel.sdl')
    if name=='Utils.java':
        s=s.replace('context.getExternalFilesDir(null)','new File(context.getFilesDir(), "joyorbit")').replace('return createDirs(extDir, "Minetest");','return createDirs(extDir, "voxel");')
    if name=='GameActivity.java':
        a=s.index('\tprivate void updateGameNotification()');b=s.index('\n\tpublic void setPlayingNowNotification',a)
        s=s[:a]+'\tprivate void updateGameNotification() {}\n\n'+s[b:]
    (parent/name).write_text(s)
for name in ('JoyOrbitVoxeLibreActivity.java','JoyOrbitVoxeLibreLaunchActivity.java'):
    target=java/'io/precisiondata/joyorbit/voxel'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/'android/luanti'/name,target)
with zipfile.ZipFile(native) as archive:
    target=module/'jniLibs/arm64-v8a';target.mkdir(parents=True,exist_ok=True)
    target.joinpath('libjoyorbit_voxel.so').write_bytes(archive.read('jni/arm64-v8a/libluanti.so'))
assets=module/'assets/joyorbit/voxel/data';assets.mkdir(parents=True,exist_ok=True)
for name in ('builtin','textures/base/pack','client/shaders','fonts'):
    shutil.copytree(work/name,assets/name,dirs_exist_ok=True,ignore=shutil.ignore_patterns('CMakeLists.txt'))
if (work/'irr/media/Shaders').is_dir():
    shutil.copytree(work/'irr/media/Shaders',assets/'client/shaders/Irrlicht',dirs_exist_ok=True)
game=ROOT/'.sources/voxelibre';dest=assets/'games/mineclone2';dest.mkdir(parents=True,exist_ok=True)
for name in ('mods','textures','menu','locale'):
    if (game/name).is_dir():shutil.copytree(game/name,dest/name,dirs_exist_ok=True)
for name in ('game.conf','minetest.conf','LICENSE.txt','CREDITS.md','README.md','LEGAL.md','HOW_TO_PLAY.md'):
    shutil.copy2(game/name,dest/name)
shutil.copy2(work/'doc/lgpl-2.1.txt',assets/'Luanti-LGPL2.1.txt')
# AAPT's default _* filter strips VoxeLibre's internal mod directories. Archive
# the complete data tree and load it privately so every licensed file survives.
archive_path=module/'packed-assets/joyorbit/voxel/data.zip'
archive_path.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive_path,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for file in sorted(assets.rglob('*')):
        if file.is_file():archive.write(file,file.relative_to(assets).as_posix())
res=module/'res/values';res.mkdir(parents=True,exist_ok=True)
(res/'styles.xml').write_text('<resources><style name="JoyOrbitVoxeLibreTheme" parent="Theme.AppCompat.NoActionBar"><item name="android:windowFullscreen">true</item><item name="android:windowBackground">#0e1014</item></style></resources>')
(res/'strings.xml').write_text('<resources><string name="ime_dialog_done">Done</string><string name="no_web_browser">External links are unavailable in this game.</string></resources>')
(module/'AndroidManifest.xml').write_text('''<manifest xmlns:android="http://schemas.android.com/apk/res/android">
<!-- Luanti's internal single-player client/server communicates over loopback. -->
<uses-permission android:name="android.permission.INTERNET"/>
<application>
<activity android:name="io.precisiondata.joyorbit.voxel.JoyOrbitVoxeLibreLaunchActivity" android:exported="true" android:process=":voxelprep" android:screenOrientation="landscape" android:theme="@android:style/Theme.NoTitleBar.Fullscreen"/>
<activity android:name="io.precisiondata.joyorbit.voxel.JoyOrbitVoxeLibreActivity" android:exported="false" android:process=":voxel" android:launchMode="singleInstance" android:screenOrientation="landscape" android:enableOnBackInvokedCallback="false" android:configChanges="orientation|keyboard|keyboardHidden|navigation|screenSize|smallestScreenSize|screenLayout|uiMode" android:theme="@style/JoyOrbitVoxeLibreTheme"/>
</application></manifest>''')
for name in ('gradlew','gradlew.bat'):shutil.copy2(ROOT/'.sources/retroarch/pkg/android/phoenix'/name,module/name)
shutil.copytree(ROOT/'.sources/retroarch/pkg/android/phoenix/gradle',module/'gradle',dirs_exist_ok=True)
(module/'settings.gradle').write_text('rootProject.name="luanti-embedded"\n')
(module/'local.properties').write_text('sdk.dir='+os.environ['ANDROID_SDK_ROOT']+'\n')
(module/'gradle.properties').write_text('android.useAndroidX=true\norg.gradle.jvmargs=-Xmx3g\n')
(module/'build.gradle').write_text('''buildscript { repositories { google(); mavenCentral() }; dependencies { classpath 'com.android.tools.build:gradle:9.1.0' } }
repositories { google(); mavenCentral() }
apply plugin: 'com.android.library'
android {
 namespace 'net.minetest.minetest'
 compileSdk 36
 defaultConfig { minSdk 24 }
 sourceSets { main { manifest.srcFile 'AndroidManifest.xml'; java.srcDirs=['java']; res.srcDirs=['res']; jniLibs.srcDirs=['jniLibs']; assets.srcDirs=['packed-assets'] } }
}
dependencies { implementation 'androidx.appcompat:appcompat:1.7.1'; implementation 'androidx.core:core:1.17.0' }
''')
subprocess.run(['sh',str(module/'gradlew'),'-p',str(module),'assembleDebug','--no-daemon'],check=True)
out=ROOT/'build/android-apk/libs';out.mkdir(parents=True,exist_ok=True)
shutil.copy2(module/'build/outputs/aar/luanti-embedded-debug.aar',out/'joyorbit-voxel.aar')
shutil.copy2(work/'doc/lgpl-2.1.txt',ROOT/'theme/licenses/Luanti-LGPL2.1.txt')
shutil.copy2(game/'LICENSE.txt',ROOT/'theme/licenses/VoxeLibre-GPL3.txt')
shutil.copy2(game/'CREDITS.md',ROOT/'theme/licenses/VoxeLibre-credits.txt')
shutil.copy2(game/'LEGAL.md',ROOT/'theme/licenses/VoxeLibre-media.txt')
print('VoxeLibre embedded for offline-world testing. Physical acceptance and full dependency/asset review remain open.')
