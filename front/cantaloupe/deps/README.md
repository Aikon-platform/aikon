# About This Folder

This folder contains native binaries needed by KakaduDemoProcessor and
KakaduNativeProcessor.

Inside each platform-specific folder are `bin` and `lib` folders:

* The `bin` folder contains `kdu_expand`, one of the demo tools needed by
  KakaduDemoProcessor. These can also be downloaded from the
  [Kakadu website](http://kakadusoftware.com/downloads/).
* The `lib` folder contains the Kakadu shared library needed by both
  `kdu_expand` and `KakaduNativeProcessor`.

See the user manual -> Processors section -> KakaduDemoProcessor &
KakaduNativeProcessor sections for setup steps.

# License

All of the software in this directory tree is distributed under a Kakadu Public
Service License, which means that it may only be used for non-commercial
purposes that are solely for the public good. See the
[Kakadu License Terms](http://kakadusoftware.com/wp-content/uploads/2014/06/Kakadu-Licence-Terms-Feb-2018.pdf)
document for detailed terms of use.

# Build Info

## Linux

The Linux binaries were compiled on CentOS 7 x86 64-bit with gcc 4.8.5.

```
cd coresys/make
make -f Makefile-Linux-x86-64-gcc
cd ../../managed/make
make -f Makefile-Linux-x86-64-gcc
cd ../../lib/Linux-x86-64-gcc

# Builds libkdu_vNXX.so & libkdu_jni.so
# Java class files are in ../../../java/kdu_jni
```

## macOS

The macOS binaries were compiled on macOS 10.13.4 with xcodebuild and
clang 902.0.39.1, for target `x86_64-apple-darwin17.5.0`.

```
cd managed
xcodebuild -project managed.xcodeproj -target kdu_jni -configuration Release clean
xcodebuild -project managed.xcodeproj -target kdu_jni -configuration Release

# Resulting binaries are in ../../bin
# Java class files are in ../../java/kdu_jni
```

## Windows

The Windows binaries were compiled on Windows 7 SP1 64-bit with Visual
Studio Community 2015.

### Build Steps

1. Install the JDK
2. Install Visual Studio with the Microsoft Foundation Classes for C++
   component
3. Build `coresys`
    1. Open `coresys\coresys_2015`
    2. Retarget solution to the 8.1 platform version
    3. Build with Release configuration & x64 platform
4. Build `kdu_jni`
    1. Open `managed\kdu_managed_2015`
    2. Add the JDK headers to the include path
        1. Right-click on the `kdu_jni` solution
        2. Go to Properties -> VC++ Directories -> Include Directories
        3. Add path to JDK headers
    3. Retarget solution to the 8.1 platform version
    4. Build with Release configuration & x64 platform
5. Build `kdu_expand`
    1. Open `apps\apps_2015`
    2. Retarget the `kdu_expand` solution to the 8.1 platform version
    3. Build with Release configuration & x64 platform

The resulting files are in `..\..\bin_x64`:
  * `kdu_v7AR.dll`
  * `kdu_a7AR.dll`
  * `kdu_jni.dll`
  * `kdu_expand.exe`
