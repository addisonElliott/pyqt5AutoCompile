import os
import time

import pytest

from .. import pyqt5ac


def _is_gitlab_ci():
    return os.getenv("GITLAB_CI") is not None


def _assert_path_exists(expected_path):
    assert expected_path.check(), ("Generated file does not exist " + str(expected_path))


def _assert_path_does_not_exist(expected_path):
    assert not expected_path.check(), ("Generated file exists " + str(expected_path))


def _assert_empty_file_exists(empty_file):
    _assert_path_exists(empty_file)
    assert "" == empty_file.read()


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


def _write_config_file_with_variables(dir, variable_name, variable_value):
    config = dir.join("input_config.yml")
    config.write("""variables:
  {variable_name}: {variable_value}
ioPaths:
  -
    - '%%{variable_name}%%/gui/*.ui'
    - '%%{variable_name}%%/generated/%%FILENAME%%_ui.py'
  -
    - '%%{variable_name}%%/resources/*.qrc'
    - '%%{variable_name}%%/generated/%%FILENAME%%_rc.py'""".format(variable_name=variable_name,
                                                                   variable_value=variable_value))

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
    _assert_empty_file_exists(tmpdir.join("generated/__init__.py"))


def test_resource_generation(tmpdir):
    config = _write_config_file(tmpdir)
    resource_file = tmpdir.mkdir("resources").join("resource.qrc")
    _write_resource_file(resource_file)

    example_image = tmpdir.join("resources/example.png")
    example_image.write("test")

    pyqt5ac.main(config=str(config))

    _assert_path_exists(tmpdir.join("generated"))
    _assert_path_exists(tmpdir.join("generated/resource_rc.py"))
    _assert_empty_file_exists(tmpdir.join("generated/__init__.py"))


def test_ui_generation_when_up_to_date(tmpdir):
    config = _write_config_file(tmpdir)
    ui_file = tmpdir.mkdir("gui").join("main.ui")
    _write_ui_file(ui_file)

    dest_file = tmpdir.mkdir("generated").join("main_ui.py")
    dest_file.write("test")
    modification_time = dest_file.mtime()

    pyqt5ac.main(config=str(config))

    _assert_path_exists(tmpdir.join("generated"))
    _assert_empty_file_exists(tmpdir.join("generated/__init__.py"))
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
    _assert_empty_file_exists(tmpdir.join("generated/__init__.py"))
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
    _assert_empty_file_exists(tmpdir.join("generated/__init__.py"))
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
    _assert_empty_file_exists(tmpdir.join("generated/__init__.py"))
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
    _assert_empty_file_exists(tmpdir.join("generated/__init__.py"))
    dest_file = tmpdir.join("generated/resource_rc.py")
    _assert_path_exists(dest_file)
    assert dest_mod_time != dest_file.mtime()
    assert "test" != dest_file.read()


def test_generation_fails_with_forbidden_filename_variable(tmpdir):
    run_forbidden_variable_case(tmpdir, 'FILENAME')


def test_generation_fails_with_forbidden_ext_variable(tmpdir):
    run_forbidden_variable_case(tmpdir, 'EXT')


def test_generation_fails_with_forbidden_dirname_variable(tmpdir):
    run_forbidden_variable_case(tmpdir, 'DIRNAME')


def run_forbidden_variable_case(tmpdir, variable):
    config = _write_config_file_with_variables(tmpdir, variable, 'value')

    with pytest.raises(ValueError):
        pyqt5ac.main(config=str(config))


def test_ui_generation_when_invalid(tmpdir):
    config = _write_config_file(tmpdir)
    ui_file = tmpdir.mkdir("gui").join("main.ui")
    ui_file.write("invalid_content")

    pyqt5ac.main(config=str(config))

    assert tmpdir.join("generated").check()
    _assert_empty_file_exists(tmpdir.join("generated/__init__.py"))
    # TODO generated file should not exist and pyqt5ac should fail
    assert tmpdir.join("generated/main_ui.py").check()


def test_ui_generation_with_variables(tmpdir):
    config = _write_config_file_with_variables(tmpdir, 'BASENAME', str(tmpdir))
    ui_file = tmpdir.mkdir("gui").join("main.ui")
    _write_ui_file(ui_file)

    pyqt5ac.main(config=str(config), uicOptions="-d")

    _assert_path_exists(tmpdir.join("generated"))
    _assert_empty_file_exists(tmpdir.join("generated/__init__.py"))
    _assert_path_exists(tmpdir.join("generated/main_ui.py"))


def test_init_is_untouched(tmpdir):
    config = _write_config_file(tmpdir)
    ui_file = tmpdir.mkdir("gui").join("main.ui")
    _write_ui_file(ui_file)
    init_file = tmpdir.mkdir("generated").join("__init__.py")
    init_file.write("test")

    pyqt5ac.main(config=str(config))

    _assert_path_exists(tmpdir.join("generated"))
    _assert_path_exists(tmpdir.join("generated/main_ui.py"))
    _assert_path_exists(tmpdir.join("generated/__init__.py"))
    assert "test" == init_file.read()


def test_dont_check_for_init(tmpdir):
    config = _write_config_file(tmpdir)
    ui_file = tmpdir.mkdir("gui").join("main.ui")
    _write_ui_file(ui_file)

    pyqt5ac.main(config=str(config), initPackage=False)

    _assert_path_exists(tmpdir.join("generated"))
    _assert_path_exists(tmpdir.join("generated/main_ui.py"))
    _assert_path_does_not_exist(tmpdir.join("generated/__init__.py"))


def test_relative_paths_are_relative_to_their_config_file(tmpdir):
    config = _write_config_file(tmpdir)
    ui_file = tmpdir.mkdir("gui").join("main.ui")
    _write_ui_file(ui_file)
    tmpdir.mkdir("another_directory")
    os.chdir(str(tmpdir.join("another_directory")))  # Python3.5 compatibility

    pyqt5ac.main(config=str(config))

    _assert_path_exists(tmpdir.join("generated"))
    _assert_path_exists(tmpdir.join("generated/main_ui.py"))


def test_relative_paths_are_relative_to_cwd_if_no_config_file_is_given(tmpdir):
    ui_file = tmpdir.mkdir("another_directory").mkdir("gui").join("main.ui")
    _write_ui_file(ui_file)
    os.chdir(str(tmpdir.join("another_directory")))  # Python3.5 compatibility

    pyqt5ac.main(uicOptions='--from-imports', force=False, initPackage=True, ioPaths=[
        ['gui/*.ui', 'generated/%%FILENAME%%_ui.py'],
    ])

    _assert_path_does_not_exist(tmpdir.join("generated"))
    _assert_path_does_not_exist(tmpdir.join("generated/main_ui.py"))
    _assert_path_exists(tmpdir.join("another_directory").join("generated"))
    _assert_path_exists(tmpdir.join("another_directory").join("generated/main_ui.py"))


def test_absolute_paths_stay_untouched(tmpdir):
    dir1 = tmpdir.mkdir("dir1")
    dir2 = tmpdir.mkdir("dir2")
    dir3 = tmpdir.mkdir("dir3")

    ui_file = dir2.mkdir("gui").join("main.ui")
    _write_ui_file(ui_file)

    os.chdir(str(dir1))  # Python3.5 compatibility
    pyqt5ac.main(uicOptions='--from-imports', force=False, initPackage=True, ioPaths=[
        [str(dir2.join('gui/*.ui')), str(dir3.join('generated/%%FILENAME%%_ui.py'))],
    ])

    _assert_path_does_not_exist(tmpdir.join("generated"))
    _assert_path_does_not_exist(tmpdir.join("generated/main_ui.py"))
    _assert_path_exists(dir3.join("generated"))
    _assert_path_exists(dir3.join("generated/main_ui.py"))


def test_config_file_path_is_relative_to_cwd(tmpdir):
    another_dir = tmpdir.mkdir("another_directory")
    _write_config_file(another_dir)
    ui_file = another_dir.mkdir("gui").join("main.ui")
    _write_ui_file(ui_file)

    os.chdir(str(another_dir))  # Python3.5 compatibility
    pyqt5ac.main(config="input_config.yml")

    _assert_path_exists(another_dir.join("generated"))
    _assert_path_exists(another_dir.join("generated/main_ui.py"))

    os.chdir(str(tmpdir))  # Python3.5 compatibility
    with pytest.raises(FileNotFoundError):
        pyqt5ac.main(config="input_config.yml")


