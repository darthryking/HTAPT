Hazard Team Asset Pruning Tool
==========

Copyright © 2015 by DKY (Ryan Lam)

The __Hazard Team Asset Pruning Tool (HTAPT)__ is an experimental tool for Source Engine modders. It is intended to be used for analyzing a mod's dependencies to determine which assets in the file system are unused in the mod, so that the user may clean up those files and save valuable disk space and mod size.

It uses a very simple mark-and-sweep algorithm to walk through the mod's dependency tree, starting from a set of root files that are known to be required for the mod to function. It currently requires that you include a `src` folder full of your maps' VMFs (described below), though this is probably going to change in the future.


Current version: ___0.0.0 DEV___


###Requirements
* Python 2.7

###To Run
1. Place `htapt.py` in the folder directly enclosing the root project folder of your mod.
2. Make sure the `BASE_DIR` variable is set to the name of your mod's root project folder.
3. Add a folder named `src` to your mod's `maps/` directory, and put all `*.vmf` files in that directory.
4. Modify the `ROOT_FILES` tuple in the `main()` function to match your mod's root file setup, including the VMFs.
5. Run `htapt.py`.
6. HTAPT will walk your mod's asset dependency tree starting from the root files, and output a list of unused assets (`sweep.txt`) that are ureachable from the dependency tree.
7. Done!
