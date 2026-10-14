package io.precisiondata.joyorbit.voxel;

import android.app.Activity;
import android.os.Bundle;
import java.io.*;

public final class JoyOrbitVoxeLibreLaunchActivity extends Activity {
    private volatile boolean cancelled;
    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        android.widget.TextView label = new android.widget.TextView(this);
        label.setText("Starting VoxeLibre…");
        label.setTextColor(0xff8ee5c0);
        label.setTextSize(28);
        label.setGravity(android.view.Gravity.CENTER);
        label.setBackgroundColor(0xff0e1014);
        setContentView(label);
        new Thread(() -> {
            try {
                File root = new File(getFilesDir(), "joyorbit/voxel");
                File stamp = new File(root, ".source-c0e6812-a523240-zip1");
                if (!stamp.isFile()) {
                    extractData(root);
                    try (FileOutputStream output = new FileOutputStream(stamp)) { output.write(1); }
                }
                File world = new File(root,"worlds/joyorbit");
                world.mkdirs();
                writeIfAbsent(new File(world,"world.mt"),
                    "gameid = mineclone2\nworld_name = JoyOrbit World\nbackend = sqlite3\nplayer_backend = sqlite3\nauth_backend = sqlite3\n");
                boolean tv = (getResources().getConfiguration().uiMode & android.content.res.Configuration.UI_MODE_TYPE_MASK)
                    == android.content.res.Configuration.UI_MODE_TYPE_TELEVISION;
                writeIfAbsent(new File(root,"joyorbit.conf"),
                    "language = en\ncreative_mode = true\nenable_damage = false\nserver_announce = false\n"+
                    "enable_ipv6 = false\nbind_address = 127.0.0.1\nenable_remote_media_server = false\n"+
                    "enable_client_modding = false\nenable_sscsm = nowhere\nauto_update_check = false\n"+
                    "show_debug = false\nkeymap_screenshot = SYSTEM_SCANCODE_69\n"+
                    "keymap_zoom = SYSTEM_SCANCODE_29\nkeymap_drop = SYSTEM_SCANCODE_20\n"+
                    "keymap_freemove = SYSTEM_SCANCODE_14\n"+
                    "fps_max = 60\nviewing_range = 70\ntouch_controls = " + (tv ? "false" : "true") +
                    "\ntouch_gui = " + (tv ? "false" : "true") + "\n"+
                    "keymap_forward = SYSTEM_SCANCODE_26|GAMEPAD_AXIS_MINUS_1|GAMEPAD_BUTTON_11\n"+
                    "keymap_backward = SYSTEM_SCANCODE_22|GAMEPAD_AXIS_PLUS_1|GAMEPAD_BUTTON_12\n"+
                    "keymap_left = SYSTEM_SCANCODE_4|GAMEPAD_AXIS_MINUS_0|GAMEPAD_BUTTON_13\n"+
                    "keymap_right = SYSTEM_SCANCODE_7|GAMEPAD_AXIS_PLUS_0|GAMEPAD_BUTTON_14\n");
                runOnUiThread(() -> {
                    if (cancelled) return;
                    startActivity(new android.content.Intent(this, JoyOrbitVoxeLibreActivity.class));
                    finish();
                });
            } catch (IOException failure) {
                android.util.Log.e("JoyOrbit", "VoxeLibre preparation failed", failure);
                runOnUiThread(() -> label.setText("VoxeLibre could not start. Return to the library and try again."));
            }
        }, "JoyOrbit sandbox data").start();
    }
    private void writeIfAbsent(File file, String value) throws IOException {
        if (file.isFile()) return;
        try (FileOutputStream output = new FileOutputStream(file)) {
            output.write(value.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        }
    }
    private void extractData(File root) throws IOException {
        root.mkdirs();
        String prefix = root.getCanonicalPath() + File.separator;
        try (java.util.zip.ZipInputStream zip = new java.util.zip.ZipInputStream(
                getAssets().open("joyorbit/voxel/data.zip"))) {
            java.util.zip.ZipEntry entry;
            byte[] bytes = new byte[65536];
            while ((entry = zip.getNextEntry()) != null) {
                File target = new File(root,entry.getName());
                if (!target.getCanonicalPath().startsWith(prefix)) throw new IOException("Invalid game archive path");
                if (entry.isDirectory()) {
                    if (!target.isDirectory() && !target.mkdirs()) throw new IOException("Cannot prepare game directory");
                    continue;
                }
                File parent = target.getParentFile();
                if (!parent.isDirectory() && !parent.mkdirs()) throw new IOException("Cannot prepare game directory");
                File temporary = new File(parent,target.getName()+".new");
                try (FileOutputStream output = new FileOutputStream(temporary)) {
                    int count;
                    while ((count = zip.read(bytes)) != -1) output.write(bytes,0,count);
                }
                if (!temporary.renameTo(target)) throw new IOException("Cannot finish game extraction");
                zip.closeEntry();
            }
        }
    }
    @Override public void onDestroy() { cancelled = true; super.onDestroy(); }
}
