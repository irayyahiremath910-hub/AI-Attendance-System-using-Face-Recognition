import sys, os, platform, traceback, sysconfig
print('PYTHON:', sys.executable)
print('PYTHON VERSION:', sys.version)
print('PLATFORM:', platform.platform())
print('MACHINE:', platform.machine())
print('PREFIX:', sys.prefix)
# show site-packages
site_packages = sysconfig.get_paths().get('purelib')
print('site-packages:', site_packages)
if site_packages and os.path.isdir(site_packages):
    try:
        files = os.listdir(site_packages)
        print('sample site-packages entries:', files[:20])
    except Exception as e:
        print('ls site-packages failed:', e)
# pip show torch
try:
    import subprocess, shlex
    out = subprocess.check_output([sys.executable, '-m', 'pip', 'show', 'torch'], stderr=subprocess.STDOUT, text=True)
    print('\nPIP SHOW TORCH:\n', out)
except Exception as e:
    print('pip show torch failed:', e)
# list torch package files
torch_dir = None
candidates = []
if site_packages:
    for name in ('torch', 'torch-*'):
        p = os.path.join(site_packages, 'torch')
        candidates.append(p)
        if os.path.isdir(p):
            torch_dir = p
            break
if torch_dir:
    print('\nTORCH DIR:', torch_dir)
    try:
        files = os.listdir(torch_dir)
        print('torch dir entries:', files[:100])
    except Exception as e:
        print('list torch dir failed:', e)
    # find compiled _C file
    pyd_candidates = [f for f in files if f.startswith('_C') or f.endswith('.pyd') or f.endswith('.dll')]
    print('pyd candidates in torch dir:', pyd_candidates)
    for f in pyd_candidates:
        full = os.path.join(torch_dir, f)
        print('\nTrying to load binary:', full)
        try:
            if platform.system() == 'Windows':
                import ctypes
                ctypes.WinDLL(full)
                print('Loaded OK via WinDLL')
        except Exception as e:
            print('WinDLL load failed:', type(e).__name__, e)
            traceback.print_exc()
else:
    print('\nTORCH package not found in site-packages')
# attempt import to show full traceback
print('\nATTEMPTING: import torch (to capture original traceback)')
try:
    import torch
    print('import torch succeeded, version:', getattr(torch, '__version__', 'unknown'))
except Exception as e:
    print('IMPORT ERROR:', type(e).__name__, e)
    traceback.print_exc()
