import sys

from PySide2.QtWidgets import QApplication

from mapeditor.window import MapEditorWindow


def main(args):
    app = QApplication(args)
    editor = MapEditorWindow()
    editor.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main(sys.argv)
