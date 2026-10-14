package io.precisiondata.joyorbit.voxel;

public final class JoyOrbitVoxeLibreActivity extends net.minetest.minetest.GameActivity {
    private boolean startDown, selectDown;
    private final android.os.Handler returnHandler = new android.os.Handler(android.os.Looper.getMainLooper());
    private final Runnable longBackReturn = () -> nativeSendQuit();
    @Override protected String[] getLibraries() { return new String[] {"joyorbit_voxel"}; }
    @Override protected String getMainSharedObject() {
        return getApplicationInfo().nativeLibraryDir + "/libjoyorbit_voxel.so";
    }
    @Override protected String[] getArguments() {
        java.io.File root = new java.io.File(getFilesDir(), "joyorbit/voxel");
        return new String[] {"--go", "--world", new java.io.File(root,"worlds/joyorbit").getAbsolutePath(),
            "--gameid", "mineclone2", "--config", new java.io.File(root,"joyorbit.conf").getAbsolutePath(),
            "--name", "JoyOrbit", "--logfile", new java.io.File(root,"engine.log").getAbsolutePath()};
    }
    @Override public String getLanguage() { return "en"; }
    @Override public void openURI(String uri) { /* Offline game; no external navigation. */ }
    @Override public void shareFile(String path) { /* Exports are not part of this game flow. */ }
    @Override public void onWindowFocusChanged(boolean focused) {
        if (!focused) { startDown = false; selectDown = false; returnHandler.removeCallbacks(longBackReturn); }
        super.onWindowFocusChanged(focused);
    }
    @Override public boolean dispatchKeyEvent(android.view.KeyEvent event) {
        if (event.getKeyCode() == android.view.KeyEvent.KEYCODE_BACK) {
            if (event.getAction() == android.view.KeyEvent.ACTION_DOWN && event.getRepeatCount() == 0)
                returnHandler.postDelayed(longBackReturn, 700);
            else if (event.getAction() == android.view.KeyEvent.ACTION_UP)
                returnHandler.removeCallbacks(longBackReturn);
        }
        if (event.getKeyCode() == android.view.KeyEvent.KEYCODE_BUTTON_START)
            startDown = event.getAction() == android.view.KeyEvent.ACTION_DOWN;
        if (event.getKeyCode() == android.view.KeyEvent.KEYCODE_BUTTON_SELECT)
            selectDown = event.getAction() == android.view.KeyEvent.ACTION_DOWN;
        if ((startDown && selectDown && event.getAction() == android.view.KeyEvent.ACTION_DOWN) ||
            (event.getKeyCode() == android.view.KeyEvent.KEYCODE_BACK && event.isLongPress())) {
            nativeSendQuit();
            return true;
        }
        return super.dispatchKeyEvent(event);
    }
    @Override public void onDestroy() {
        returnHandler.removeCallbacks(longBackReturn);
        super.onDestroy();
        android.os.Process.killProcess(android.os.Process.myPid());
    }
}
