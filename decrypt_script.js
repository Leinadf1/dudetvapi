Java.perform(function() {
    try {
        console.log("[Frida JS] Running decryption...");
        
        // 1. Load DataHelper
        var DataHelper = Java.use("com.sportzx.live.helpers.DataHelper");
        var instance = DataHelper.INSTANCE.value;
        if (!instance) {
            console.log("[Frida JS] Creating new DataHelper instance...");
            instance = DataHelper.$new();
        }
        
        // 2. Get Context
        var ActivityThread = Java.use("android.app.ActivityThread");
        var context = ActivityThread.currentApplication().getApplicationContext();
        
        // 3. Read payload from /data/local/tmp/payload.txt via Java
        var File = Java.use("java.io.File");
        var FileInputStream = Java.use("java.io.FileInputStream");
        var BufferedReader = Java.use("java.io.BufferedReader");
        var InputStreamReader = Java.use("java.io.InputStreamReader");
        
        var payloadFile = File.$new("/data/local/tmp/payload.txt");
        if (!payloadFile.exists()) {
            console.log("[Frida JS] ERROR: /data/local/tmp/payload.txt does not exist!");
            return;
        }
        
        var fis = FileInputStream.$new(payloadFile);
        var isr = InputStreamReader.$new(fis, "UTF-8");
        var br = BufferedReader.$new(isr);
        
        var sb = Java.use("java.lang.StringBuilder").$new();
        var line = null;
        while ((line = br.readLine()) !== null) {
            sb.append(line);
        }
        br.close();
        
        var payload = sb.toString();
        console.log("[Frida JS] Loaded payload of length: " + payload.length);
        
        // 4. Call JNI help
        console.log("[Frida JS] Invoking JNI help()...");
        var decryptedStr = instance.help(context, payload);
        if (decryptedStr === null) {
            console.log("[Frida JS] ERROR: help() returned null");
            return;
        }
        console.log("[Frida JS] Decrypted string length: " + decryptedStr.length);
        
        // 5. Get bytes via UTF-16BE by converting JS string to Java String
        var JavaString = Java.use("java.lang.String");
        var javaStr = JavaString.$new(decryptedStr);
        var bytes = javaStr.getBytes("UTF-16BE");
        console.log("[Frida JS] UTF-16BE bytes length: " + bytes.length);
        
        // Write bytes to decrypted_raw.bin inside app's private cache folder (for write permission)
        var FileOutputStream = Java.use("java.io.FileOutputStream");
        var cachePath = context.getCacheDir().getAbsolutePath();
        var outFilePath = cachePath + "/decrypted_raw.bin";
        var outFile = File.$new(outFilePath);
        var fos = FileOutputStream.$new(outFile);
        fos.write(bytes);
        fos.close();
        
        console.log("[Frida JS] SUCCESS! Decrypted raw bytes saved to: " + outFilePath);
        
    } catch (e) {
        console.log("[Frida JS] Exception: " + e + "\n" + e.stack);
    }
});
