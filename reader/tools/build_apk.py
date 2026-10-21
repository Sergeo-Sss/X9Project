"""Build and sign the X9 Reader APK using only Android SDK command-line tools.

Pipeline: aapt2 link (manifest + assets) -> javac -> d8 -> inject classes.dex ->
zipalign -> apksigner (debug key). No Gradle, no Android Studio.
"""
import os
import shutil
import subprocess
import sys
import zipfile

SDK = r"D:\Android\Sdk"
BUILD_TOOLS = os.path.join(SDK, "build-tools", "36.0.0")
ANDROID_JAR = os.path.join(SDK, "platforms", "android-34", "android.jar")

APP = r"D:\Projects\X9Project\reader\app"
OUT = r"D:\Projects\X9Project\reader\build"
TOOLS = r"D:\Projects\X9Project\reader\tools"
KEYSTORE = os.path.join(TOOLS, "debug.keystore")

MANIFEST = os.path.join(APP, "AndroidManifest.xml")
ASSETS = os.path.join(APP, "assets")
SRC = os.path.join(APP, "src")


def tool(name):
    for ext in (".bat", ".exe", ".cmd", ""):
        p = os.path.join(BUILD_TOOLS, name + ext)
        if os.path.exists(p):
            return p
    raise SystemExit(f"tool not found: {name} in {BUILD_TOOLS}")


def run(cmd, **kw):
    print(">", " ".join(f'"{c}"' if " " in c else c for c in cmd))
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.stdout.strip():
        print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stderr.strip())
        raise SystemExit(f"FAILED ({r.returncode}): {cmd[0]}")
    if r.stderr.strip():
        print(r.stderr.strip())


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    classes = os.path.join(OUT, "classes")
    os.makedirs(classes)
    base_apk = os.path.join(OUT, "base.apk")

    # 1. Package manifest + assets into a base APK.
    run([tool("aapt2"), "link",
         "-o", base_apk,
         "-I", ANDROID_JAR,
         "--manifest", MANIFEST,
         "-A", ASSETS,
         "--min-sdk-version", "21",
         "--target-sdk-version", "26"])

    # 2. Compile Java sources (target Java 8 bytecode for d8).
    java_files = []
    for root, _, files in os.walk(SRC):
        java_files += [os.path.join(root, f) for f in files if f.endswith(".java")]
    javac = os.path.join(os.environ.get("JAVA_HOME", ""), "bin", "javac.exe")
    if not os.path.exists(javac):
        javac = "javac"
    run([javac, "-encoding", "UTF-8", "--release", "8",
         "-classpath", ANDROID_JAR, "-d", classes] + java_files)

    # 3. Dex the classes.
    class_files = []
    for root, _, files in os.walk(classes):
        class_files += [os.path.join(root, f) for f in files if f.endswith(".class")]
    run([tool("d8"), "--release", "--min-api", "21",
         "--lib", ANDROID_JAR, "--output", OUT] + class_files)

    # 4. Add classes.dex into the APK.
    dex = os.path.join(OUT, "classes.dex")
    with zipfile.ZipFile(base_apk, "a", zipfile.ZIP_DEFLATED) as z:
        z.write(dex, "classes.dex")

    # 5. Align.
    aligned = os.path.join(OUT, "aligned.apk")
    run([tool("zipalign"), "-f", "4", base_apk, aligned])

    # 6. Debug keystore (create once).
    if not os.path.exists(KEYSTORE):
        keytool = os.path.join(os.environ.get("JAVA_HOME", ""), "bin", "keytool.exe")
        if not os.path.exists(keytool):
            keytool = "keytool"
        run([keytool, "-genkeypair", "-v", "-keystore", KEYSTORE,
             "-storepass", "android", "-keypass", "android",
             "-alias", "x9", "-keyalg", "RSA", "-keysize", "2048",
             "-validity", "10000", "-dname", "CN=X9 Reader"])

    # 7. Sign.
    signed = os.path.join(OUT, "X9Reader.apk")
    run([tool("apksigner"), "sign",
         "--ks", KEYSTORE, "--ks-pass", "pass:android", "--key-pass", "pass:android",
         "--min-sdk-version", "21",
         "--out", signed, aligned])

    print("\nOK ->", signed)
    print("size:", os.path.getsize(signed), "bytes")


if __name__ == "__main__":
    main()
