import os
import time


def _is_gitlab_ci():
    return os.getenv("GITLAB_CI") is not None


if _is_gitlab_ci():
    import pyqt5ac
else:
    from .. import pyqt5ac


def _assert_path_exists(expected_path):
    assert expected_path.check(), ("Generated file does not exist " + str(expected_path))


def _wait():
    if _is_gitlab_ci():
        time.sleep(1)
    else:
        time.sleep(0.010)


def _write_config_file(dir):
    config = dir.join("input_config.yml")
    config.write("""ioPaths:
  -
    - '{dir}/gui/*.ui'
    - '{dir}/generated/%%FILENAME%%_ui.py'
  -
    - '{dir}/resources/*.qrc'
    - '{dir}/generated/%%FILENAME%%_rc.py'""".format(dir=str(dir)))

    return config


def _write_ui_file(file):
    file.write("""<?xml version="1.0" encoding="UTF-8"?>
    <ui version="4.0">
     <class>MainWidget</class>
     <widget class="QMainWindow" name="MainWidget">
      <property name="geometry">
       <rect>
        <x>0</x>
        <y>0</y>
        <width>675</width>
        <height>591</height>
       </rect>
      </property>
     </widget>
    </ui>
    """)


def _write_resource_file(file):
    file.write("""<!DOCTYPE RCC><RCC version="1.0">
    <qresource>
        <file>example.png</file>
    </qresource>
    </RCC>""")


def test_import_module():
    assert pyqt5ac.__version__ is not None


def test_without_generation(tmpdir):
    config = _write_config_file(tmpdir)

    pyqt5ac.main(config=str(config))

    assert not tmpdir.join("generated").check()


def test_ui_generation(tmpdir):
    config = _write_config_file(tmpdir)
    ui_file = tmpdir.mkdir("gui").join("main.ui")
    _write_ui_file(ui_file)

    pyqt5ac.main(config=str(config), uicOptions="-d")

    _assert_path_exists(tmpdir.join("generated"))
    _assert_path_exists(tmpdir.join("generated/main_ui.py"))


def test_resource_generation(tmpdir):
    config = _write_config_file(tmpdir)
    resource_file = tmpdir.mkdir("resources").join("resource.qrc")
    _write_resource_file(resource_file)

    example_image = tmpdir.join("resources/example.png")
    example_image.write("test")

    pyqt5ac.main(config=str(config))

    _assert_path_exists(tmpdir.join("generated"))
    _assert_path_exists(tmpdir.join("generated/resource_rc.py"))


def test_ui_generation_when_up_to_date(tmpdir):
    config = _write_config_file(tmpdir)
    ui_file = tmpdir.mkdir("gui").join("main.ui")
    _write_ui_file(ui_file)

    dest_file = tmpdir.mkdir("generated").join("main_ui.py")
    dest_file.write("test")
    modification_time = dest_file.mtime()

    pyqt5ac.main(config=str(config))

    _assert_path_exists(tmpdir.join("generated"))
    dest_file = tmpdir.join("generated/main_ui.py")
    _assert_path_exists(dest_file)
    assert modification_time == dest_file.mtime()
    assert "test" == dest_file.read()


def test_ui_generation_when_out_of_date(tmpdir):
    config = _write_config_file(tmpdir)
    dest_file = tmpdir.mkdir("generated").join("main_ui.py")
    dest_file.write("test")
    dest_mod_time = dest_file.mtime()

    _wait()
    ui_file = tmpdir.mkdir("gui").join("main.ui")
    _write_ui_file(ui_file)
    source_mod_time = ui_file.mtime()

    assert source_mod_time > dest_mod_time

    pyqt5ac.main(config=str(config))

    _assert_path_exists(tmpdir.join("generated"))
    dest_file = tmpdir.join("generated/main_ui.py")
    _assert_path_exists(dest_file)
    assert dest_mod_time != dest_file.mtime()
    assert "test" != dest_file.read()


def test_resource_generation_when_up_to_date(tmpdir):
    config = _write_config_file(tmpdir)
    resource_file = tmpdir.mkdir("resources").join("resource.qrc")
    _write_resource_file(resource_file)

    example_image = tmpdir.join("resources/example.png")
    example_image.write("test")

    dest_file = tmpdir.mkdir("generated").join("main_rc.py")
    dest_file.write("test")
    modification_time = dest_file.mtime()

    pyqt5ac.main(config=str(config))

    _assert_path_exists(tmpdir.join("generated"))
    dest_file = tmpdir.join("generated/main_rc.py")
    _assert_path_exists(dest_file)
    assert modification_time == dest_file.mtime()
    assert "test" == dest_file.read()


def test_resource_generation_when_resource_out_of_date(tmpdir):
    config = _write_config_file(tmpdir)
    tmpdir.mkdir("resources")
    example_image = tmpdir.join("resources/example.png")
    example_image.write("test")

    dest_file = tmpdir.mkdir("generated").join("resource_rc.py")
    dest_file.write("test")
    dest_mod_time = dest_file.mtime()

    _wait()
    resource_file = tmpdir.join("resources/resource.qrc")
    _write_resource_file(resource_file)
    source_mod_time = resource_file.mtime()

    assert source_mod_time > dest_mod_time
    pyqt5ac.main(config=str(config))

    _assert_path_exists(tmpdir.join("generated"))
    dest_file = tmpdir.join("generated/resource_rc.py")
    _assert_path_exists(dest_file)
    assert dest_mod_time != dest_file.mtime()
    assert "test" != dest_file.read()


def test_resource_generation_when_image_out_of_date(tmpdir):
    config = _write_config_file(tmpdir)
    tmpdir.mkdir("resources")
    resource_file = tmpdir.join("resources/resource.qrc")
    _write_resource_file(resource_file)

    dest_file = tmpdir.mkdir("generated").join("resource_rc.py")
    dest_file.write("test")
    dest_mod_time = dest_file.mtime()

    _wait()
    example_image = tmpdir.join("resources/example.png")
    example_image.write("test")

    pyqt5ac.main(config=str(config))

    _assert_path_exists(tmpdir.join("generated"))
    dest_file = tmpdir.join("generated/resource_rc.py")
    _assert_path_exists(dest_file)
    assert dest_mod_time != dest_file.mtime()
    assert "test" != dest_file.read()


def test_ui_generation_when_invalid(tmpdir):
    config = _write_config_file(tmpdir)
    ui_file = tmpdir.mkdir("gui").join("main.ui")
    ui_file.write("invalid_content")

    pyqt5ac.main(config=str(config))

    assert tmpdir.join("generated").check()
    # TODO generated file should not exist and pyqt5ac should fail
    assert tmpdir.join("generated/main_ui.py").check()
