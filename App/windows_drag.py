"""Windows Shell file dragging; only offers copy, never move."""
from pathlib import Path


def create_file_data_object(paths):
    import pythoncom
    from win32com.shell import shell
    files = [Path(path).resolve() for path in paths]
    if not files or any(not path.is_file() for path in files):
        raise ValueError("Select existing image files first.")
    # Absolute PIDLs are relative to the Desktop namespace.
    children = [shell.SHParseDisplayName(str(path), 0)[0] for path in files]
    return shell.SHCreateDataObject([], children, None, pythoncom.IID_IDataObject)


def drag_files(paths):
    import pythoncom
    from win32com.server.util import wrap

    class DropSource:
        _com_interfaces_ = [pythoncom.IID_IDropSource]
        _public_methods_ = ["QueryContinueDrag", "GiveFeedback"]

        def QueryContinueDrag(self, escape, keys):
            if escape:
                return 0x40101  # DRAGDROP_S_CANCEL
            return 0 if keys & 1 else 0x40100  # MK_LBUTTON / DROP

        def GiveFeedback(self, effect):
            return 0x40102  # DRAGDROP_S_USEDEFAULTCURSORS

    pythoncom.OleInitialize()
    try:
        return pythoncom.DoDragDrop(create_file_data_object(paths), wrap(DropSource(), pythoncom.IID_IDropSource), 1)
    finally:
        import ctypes
        ctypes.windll.ole32.OleUninitialize()
