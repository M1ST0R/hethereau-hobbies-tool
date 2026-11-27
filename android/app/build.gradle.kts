plugins {
    id("com.android.application")
}

android {
    namespace = "com.m1stor.hhtmobile"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.m1stor.hhtmobile"
        minSdk = 26
        targetSdk = 36
        versionCode = 1
        versionName = "0.1.0-prototype"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
            versionNameSuffix = "-debug"
        }
        release {
            isMinifyEnabled = false
        }
    }
}

dependencies {
    // Bundled model: OCR works offline immediately after installation.
    implementation("com.google.mlkit:text-recognition:16.0.1")
}
