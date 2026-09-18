"""Repeat real forcefield dynamics after saving and reopening the scene."""
import runpy
import sys
from pathlib import Path
sys.argv.append('--reload')
runpy.run_path(str(Path(__file__).with_name('test_physics_dynamics.py')), run_name='__main__')
