# coding=utf-8
from setuptools import setup
import versioneer

########################################################################################################################
### Do not forget to adjust the following variables to your own plugin.

# The plugin's identifier, has to be unique
plugin_identifier = "ControlCenter"

# The plugin's python package, should be "octoprint_<plugin identifier>", has to be unique
plugin_package = "octoprint_ControlCenter"

# The plugin's human readable name. Can be overwritten within OctoPrint's internal data via __plugin_name__ in the
# plugin module
plugin_name = "Octoprint-ControlCenter"

# The plugin's version. Can be overwritten within OctoPrint's internal data via __plugin_version__ in the plugin module
plugin_version = versioneer.get_version()   # replaced by versioneer

# The plugin's description. Can be overwritten within OctoPrint's internal data via __plugin_description__ in the plugin
# module
plugin_description = """TouchScreen Plugin for Control Center"""

# The plugin's author. Can be overwritten within OctoPrint's internal data via __plugin_author__ in the plugin module
plugin_author = "Fracktal Works"

# The plugin's author's mail address.
plugin_author_email = "support@fracktal.in"

# The plugin's homepage URL. Can be overwritten within OctoPrint's internal data via __plugin_url__ in the plugin module
plugin_url = "https://github.com/FracktalWorks/ControlCenter"

# The plugin's license. Can be overwritten within OctoPrint's internal data via __plugin_license__ in the plugin module
plugin_license = "AGPLv3"

# Any additional requirements besides OctoPrint should be listed here
#plugin_requires = ['RPi.GPIO']
plugin_requires = []

### --------------------------------------------------------------------------------------------------------------------
### More advanced options that you usually shouldn't have to touch follow after this point
### --------------------------------------------------------------------------------------------------------------------

# Additional package data to install for this plugin. The subfolders "templates", "static" and "translations" will
# already be installed automatically if they exist.
# "resources" contains compiled Qt resource files (resource_rc.py + img/) required by the UI.
# Without this, the plugin fails with: ModuleNotFoundError: No module named 'ui.resources'
plugin_additional_data = ["resources"]

# Any additional python packages you need to install with your plugin that are not contains in <plugin_package>.*
plugin_addtional_packages = []

# Any python packages within <plugin_package>.* you do NOT want to install with your plugin
plugin_ignored_packages = []

# Additional parameters for the call to setuptools.setup. If your plugin wants to register additional entry points,
# define dependency links or other things like that, this is the place to go. Will be merged recursively with the
# default setup parameters as provided by octoprint_setuptools.create_plugin_setup_parameters using
# octoprint.util.dict_merge.
#
# Example:
#     plugin_requires = ["someDependency==dev"]
#     additional_setup_parameters = {"dependency_links": ["https://github.com/someUser/someRepo/archive/master.zip#egg=someDependency-dev"]}
additional_setup_parameters = {}

########################################################################################################################

from setuptools import setup


def _plain_setuptools_parameters():
    """Same result as octoprint_setuptools.create_plugin_setup_parameters, without importing OctoPrint.

    pip builds in an isolated environment (PEP 517) where OctoPrint is not importable, so a hard
    dependency on octoprint_setuptools makes `pip install <this plugin>` -- and OctoPrint's own
    software update -- fail on modern pip (OctoPrint 1.11 / Python 3.13 printers).
    """
    import os
    from setuptools import find_packages

    packages = set([plugin_package]
                   + [p for p in find_packages(exclude=plugin_ignored_packages) if p.startswith(plugin_package + ".")]
                   + list(plugin_addtional_packages))
    data = []
    for d in ["static", "templates", "translations"] + list(plugin_additional_data):
        base = os.path.join(plugin_package, d)
        for root, _, files in os.walk(base):
            data += [os.path.relpath(os.path.join(root, f), plugin_package) for f in files]
    requires = list(plugin_requires)
    if not any(r.lower().startswith("octoprint") for r in requires):
        requires = ["OctoPrint"] + requires
    return {
        "name": plugin_name, "version": plugin_version, "description": plugin_description,
        "author": plugin_author, "author_email": plugin_author_email, "url": plugin_url, "license": plugin_license,
        "packages": sorted(packages), "package_data": {plugin_package: data}, "include_package_data": True,
        "zip_safe": False, "install_requires": requires,
        "entry_points": {"octoprint.plugin": ["%s = %s" % (plugin_identifier, plugin_package)]},
    }


try:
    import octoprint_setuptools
except ImportError:
    octoprint_setuptools = None

if octoprint_setuptools is None:
    setup_parameters = _plain_setuptools_parameters()
else:
    setup_parameters = octoprint_setuptools.create_plugin_setup_parameters(
        identifier=plugin_identifier,
        package=plugin_package,
        name=plugin_name,
        version=plugin_version,
        description=plugin_description,
        author=plugin_author,
        mail=plugin_author_email,
        url=plugin_url,
        license=plugin_license,
        requires=plugin_requires,
        additional_packages=plugin_addtional_packages,
        ignored_packages=plugin_ignored_packages,
        additional_data=plugin_additional_data
    )

if len(additional_setup_parameters):
    setup_parameters.update(additional_setup_parameters)

setup(**setup_parameters)
