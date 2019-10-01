# Copyright (c) 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import pytest

from platformio.datamodel import DataFieldException
from platformio.package.manifest import parser
from platformio.package.manifest.model import ManifestModel, StrictManifestModel


def test_library_json_parser():
    contents = """
{
    "name": "TestPackage",
    "keywords": "kw1, KW2, kw3",
    "platforms": ["atmelavr", "espressif"],
    "url": "http://old.url.format",
    "exclude": [".gitignore", "tests"],
    "include": "mylib"
}
"""
    mp = parser.LibraryJsonManifestParser(contents)
    assert sorted(mp.as_dict().items()) == sorted(
        {
            "name": "TestPackage",
            "platforms": ["atmelavr", "espressif8266"],
            "export": {"exclude": [".gitignore", "tests"], "include": ["mylib"]},
            "keywords": ["kw1", "kw2", "kw3"],
            "homepage": "http://old.url.format",
        }.items()
    )

    contents = """
{
    "keywords": ["sound", "audio", "music", "SD", "card", "playback"],
    "frameworks": "arduino",
    "platforms": "atmelavr",
    "export": {
        "exclude": "audio_samples"
    }
}
"""
    mp = parser.LibraryJsonManifestParser(contents)
    assert sorted(mp.as_dict().items()) == sorted(
        {
            "keywords": ["sound", "audio", "music", "sd", "card", "playback"],
            "frameworks": ["arduino"],
            "export": {"exclude": ["audio_samples"]},
            "platforms": ["atmelavr"],
        }.items()
    )


def test_module_json_parser():
    contents = """
{
  "author": "Name Surname <name@surname.com>",
  "description": "This is Yotta library",
  "homepage": "https://yottabuild.org",
  "keywords": [
    "mbed",
    "Yotta"
  ],
  "licenses": [
    {
      "type": "Apache-2.0",
      "url": "https://spdx.org/licenses/Apache-2.0"
    }
  ],
  "name": "YottaLibrary",
  "repository": {
    "type": "git",
    "url": "git@github.com:username/repo.git"
  },
  "version": "1.2.3"
}
"""
    mp = parser.ModuleJsonManifestParser(contents)
    assert sorted(mp.as_dict().items()) == sorted(
        {
            "name": "YottaLibrary",
            "description": "This is Yotta library",
            "homepage": "https://yottabuild.org",
            "keywords": ["mbed", "Yotta"],
            "license": "Apache-2.0",
            "platforms": ["*"],
            "frameworks": ["mbed"],
            "export": {"exclude": ["tests", "test", "*.doxyfile", "*.pdf"]},
            "authors": [
                {
                    "maintainer": False,
                    "email": "name@surname.com",
                    "name": "Name Surname",
                }
            ],
            "version": "1.2.3",
        }.items()
    )


def test_library_properties_parser():
    # Base
    contents = """
name=TestPackage
version=1.2.3
author=SomeAuthor <info AT author.com>
sentence=This is Arduino library
"""
    mp = parser.LibraryPropertiesManifestParser(contents)
    assert sorted(mp.as_dict().items()) == sorted(
        {
            "name": "TestPackage",
            "version": "1.2.3",
            "description": "This is Arduino library",
            "repository": None,
            "platforms": ["*"],
            "frameworks": ["arduino"],
            "export": {
                "exclude": ["extras", "docs", "tests", "test", "*.doxyfile", "*.pdf"],
                "include": None,
            },
            "authors": [
                {"maintainer": False, "email": "info@author.com", "name": "SomeAuthor"}
            ],
            "keywords": ["uncategorized"],
            "homepage": None,
        }.items()
    )

    # Platforms ALL
    mp = parser.LibraryPropertiesManifestParser("architectures=*\n" + contents)
    assert mp.as_dict()["platforms"] == ["*"]
    # Platforms specific
    mp = parser.LibraryPropertiesManifestParser("architectures=avr, esp32\n" + contents)
    assert mp.as_dict()["platforms"] == ["atmelavr", "espressif32"]

    # Remote URL
    mp = parser.LibraryPropertiesManifestParser(
        contents,
        remote_url=(
            "https://raw.githubusercontent.com/username/reponame/master/"
            "libraries/TestPackage/library.properties"
        ),
    )
    assert mp.as_dict()["export"] == {
        "exclude": ["extras", "docs", "tests", "test", "*.doxyfile", "*.pdf"],
        "include": "libraries/TestPackage",
    }

    # Hope page
    mp = parser.LibraryPropertiesManifestParser(
        "url=https://github.com/username/reponame.git\n" + contents
    )
    assert mp.as_dict()["homepage"] is None
    assert mp.as_dict()["repository"] == {
        "type": "git",
        "url": "https://github.com/username/reponame.git",
    }


def test_library_json_model():
    contents = """
{
  "name": "ArduinoJson",
  "keywords": "JSON, rest, http, web",
  "description": "An elegant and efficient JSON library for embedded systems",
  "homepage": "https://arduinojson.org",
  "repository": {
    "type": "git",
    "url": "https://github.com/bblanchon/ArduinoJson.git"
  },
  "version": "6.12.0",
  "authors": {
    "name": "Benoit Blanchon",
    "url": "https://blog.benoitblanchon.fr"
  },
  "exclude": [
    "fuzzing",
    "scripts",
    "test",
    "third-party"
  ],
  "frameworks": "arduino",
  "platforms": "*",
  "license": "MIT",
  "examples": {
    "JsonConfigFile": {
        "base": "examples/JsonConfigFile",
        "files": ["JsonConfigFile.ino"]
    },
    "JsonHttpClient": {
        "base": "examples/JsonHttpClient",
        "files": ["JsonHttpClient.ino"]
    }
  }
}
"""
    mp = parser.ManifestParserFactory.new(
        contents, parser.ManifestFileType.LIBRARY_JSON
    )
    model = StrictManifestModel(**mp.as_dict())
    assert model.repository.url == "https://github.com/bblanchon/ArduinoJson.git"
    assert model.examples["JsonHttpClient"].files == ["JsonHttpClient.ino"]
    assert model == StrictManifestModel(
        **{
            "name": "ArduinoJson",
            "keywords": ["json", "rest", "http", "web"],
            "description": "An elegant and efficient JSON library for embedded systems",
            "homepage": "https://arduinojson.org",
            "repository": {
                "url": "https://github.com/bblanchon/ArduinoJson.git",
                "type": "git",
                "branch": None,
            },
            "version": "6.12.0",
            "authors": [
                {
                    "name": "Benoit Blanchon",
                    "url": "https://blog.benoitblanchon.fr",
                    "maintainer": False,
                    "email": None,
                }
            ],
            "export": {
                "exclude": ["fuzzing", "scripts", "test", "third-party"],
                "include": None,
            },
            "frameworks": ["arduino"],
            "platforms": ["*"],
            "license": "MIT",
            "examples": {
                "JsonConfigFile": {
                    "base": "examples/JsonConfigFile",
                    "files": ["JsonConfigFile.ino"],
                },
                "JsonHttpClient": {
                    "base": "examples/JsonHttpClient",
                    "files": ["JsonHttpClient.ino"],
                },
            },
        }
    )


def library_properties_model():
    contents = """
name=U8glib
version=1.19.1
author=oliver <olikraus@gmail.com>
maintainer=oliver <olikraus@gmail.com>
sentence=A library for monochrome TFTs and OLEDs
paragraph=Supported display controller: SSD1306, SSD1309, SSD1322, SSD1325
category=Display
url=https://github.com/olikraus/u8glib
architectures=avr,sam
"""
    mp = parser.ManifestParserFactory.new(
        contents, parser.ManifestFileType.LIBRARY_PROPERTIES
    )
    model = StrictManifestModel(**mp.as_dict())
    assert not model.get_exceptions()
    assert model == StrictManifestModel(
        **{
            "license": None,
            "description": (
                "A library for monochrome TFTs and OLEDs. Supported display "
                "controller: SSD1306, SSD1309, SSD1322, SSD1325"
            ),
            "repository": {
                "url": "https://github.com/olikraus/u8glib",
                "type": "git",
                "branch": None,
            },
            "frameworks": ["arduino"],
            "platforms": ["atmelavr", "atmelsam"],
            "version": "1.19.1",
            "export": {
                "exclude": ["extras", "docs", "tests", "test", "*.doxyfile", "*.pdf"],
                "include": None,
            },
            "authors": [
                {
                    "url": None,
                    "maintainer": True,
                    "email": "olikraus@gmail.com",
                    "name": "oliver",
                }
            ],
            "keywords": ["display"],
            "homepage": None,
            "name": "U8glib",
        }
    )


def test_platform_json_model():
    contents = """
{
  "name": "atmelavr",
  "title": "Atmel AVR",
  "description": "Atmel AVR 8- and 32-bit MCUs deliver a unique combination of performance, power efficiency and design flexibility. Optimized to speed time to market-and easily adapt to new ones-they are based on the industrys most code-efficient architecture for C and assembly programming.",
  "url": "http://www.atmel.com/products/microcontrollers/avr/default.aspx",
  "homepage": "http://platformio.org/platforms/atmelavr",
  "license": "Apache-2.0",
  "engines": {
    "platformio": "<5"
  },
  "repository": {
    "type": "git",
    "url": "https://github.com/platformio/platform-atmelavr.git"
  },
  "version": "1.15.0",
  "frameworks": {
    "arduino": {
      "package": "framework-arduinoavr",
      "script": "builder/frameworks/arduino.py"
    },
    "simba": {
      "package": "framework-simba",
      "script": "builder/frameworks/simba.py"
    }
  },
  "packages": {
    "toolchain-atmelavr": {
      "type": "toolchain",
      "version": "~1.50400.0"
    },
    "framework-arduinoavr": {
      "type": "framework",
      "optional": true,
      "version": "~4.2.0"
    },
    "framework-simba": {
      "type": "framework",
      "optional": true,
      "version": ">=7.0.0"
    },
    "tool-avrdude": {
      "type": "uploader",
      "optional": true,
      "version": "~1.60300.0"
    }
  }
}
"""
    mp = parser.ManifestParserFactory.new(
        contents, parser.ManifestFileType.PLATFORM_JSON
    )
    model = ManifestModel(**mp.as_dict())
    assert sorted(model.frameworks) == sorted(["arduino", "simba"])
    assert model == ManifestModel(
        **{
            "name": "atmelavr",
            "title": "Atmel AVR",
            "description": (
                "Atmel AVR 8- and 32-bit MCUs deliver a unique combination of "
                "performance, power efficiency and design flexibility. Optimized to "
                "speed time to market-and easily adapt to new ones-they are based "
                "on the industrys most code-efficient architecture for C and "
                "assembly programming."
            ),
            "homepage": "http://platformio.org/platforms/atmelavr",
            "license": "Apache-2.0",
            "repository": {
                "url": "https://github.com/platformio/platform-atmelavr.git",
                "type": "git",
                "branch": None,
            },
            "frameworks": ["simba", "arduino"],
            "version": "1.15.0",
        }
    )


def test_package_json_model():
    contents = """
{
    "name": "tool-scons",
    "description": "SCons software construction tool",
    "url": "http://www.scons.org",
    "version": "3.30101.0"
}
"""
    mp = parser.ManifestParserFactory.new(
        contents, parser.ManifestFileType.PACKAGE_JSON
    )
    model = ManifestModel(**mp.as_dict())
    assert model.system is None
    assert model.homepage == "http://www.scons.org"
    assert model == ManifestModel(
        **{
            "name": "tool-scons",
            "description": "SCons software construction tool",
            "homepage": "http://www.scons.org",
            "version": "3.30101.0",
        }
    )

    mp = parser.ManifestParserFactory.new(
        '{"system": "*"}', parser.ManifestFileType.PACKAGE_JSON
    )
    assert "system" not in mp.as_dict()

    mp = parser.ManifestParserFactory.new(
        '{"system": "darwin_x86_64"}', parser.ManifestFileType.PACKAGE_JSON
    )
    assert mp.as_dict()["system"] == ["darwin_x86_64"]


def test_broken_models():
    # non-strict mode
    assert len(ManifestModel(name="MyPackage").get_exceptions()) == 4
    assert ManifestModel(name="MyPackage", version="broken_version").version is None

    # strict mode

    with pytest.raises(DataFieldException) as excinfo:
        assert StrictManifestModel(name="MyPackage")
    assert excinfo.match(r"Missed value for `StrictManifestModel.[a-z]+` field")

    # broken SemVer
    with pytest.raises(
        DataFieldException,
        match="Invalid semantic versioning format for `StrictManifestModel.version` field",
    ):
        assert StrictManifestModel(
            name="MyPackage",
            description="MyDescription",
            keywords=["a", "b"],
            authors=[{"name": "Author"}],
            version="broken_version",
        )
