#!/usr/bin/env python3

import os
import logging
import subprocess
import sys

from .exceptions import (
    MissingRequirementsFileError,
    ModuleInstallationError,
    DependencyError
)


def get_installed_packages(logger: str = "main") -> dict:
    """get_installed_packages Retrieves a dictionary of installed Python packages along with their versions.

    The function executes the `pip freeze` command to obtain a list of installed packages and their respective versions. 
    It then parses the output, extracting the package names and their versions, and stores them in a dictionary where the keys are package names in lowercase, 
    and the values are the corresponding versions.

    Returns:
        dict -- A dictionary containing installed package names as keys (in lowercase) and their corresponding versions as values.
    """
    
    installed_packages = {}
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "freeze"],
            check=True,  # Raises CalledProcessError if the command fails
            capture_output=True,  # Captures stdout and stderr for debugging/logging
            text=True  # Decodes stdout/stderr as text
        )
    except subprocess.CalledProcessError as error:
        raise ModuleInstallationError(logger.error(f"An error occurred while installing dependencies:\n{error.stderr or 'Unknown error'}"))

    for line in result.stdout.split("\n"):
        if "==" in line:
            name, version = line.split("==")
            installed_packages[name.lower()] = version
    return installed_packages


def is_package_installed(package_line: str, installed_packages: dict[str, str]) -> bool:
    """is_package_installed Check if a package is installed in the given list of installed packages.

    This function determines whether a provided package from a package_line is installed by checking the installed_packages dictionary. 
    It accounts for both specific version requirements and general presence of the package.

    Arguments:
        package_line {str} -- A string representing the package, potentially including a required version, e.g., "package_name==1.0.0".
        installed_packages {dict[str, str]} -- A dictionary representing the currently installed packages. 
                                               Keys are lowercase package names and
                                               values are their installed versions.

    Returns:
        bool -- True if the package is installed with required version (if specified), or if the package is found installed without-version specification. 
                False otherwise.
    """
    
    if "==" in package_line:
        name, required_version = package_line.split("==")
        return installed_packages.get(name.lower() == required_version)
    return package_line.lower() in installed_packages


def install_requirements(path: str = "requirements", logger: str = "main"):
    """install_requirements Install required Python packages from a requirements file.

    This function enables the installation of Python package dependencies defined in a requirements file. 
    It first checks the file's existence before validating if all required packages are already installed. 
    If some packages aren't installed, it executes `pip` to install the missing dependencies. 
    The function includes optional logging features to record status, success, or error messages.

    Keyword Arguments:
        path {str} -- The path to the requirements file. (default: {"requirements"})
        logger {str} -- Choose the logger used (default: {"main"})

    Raises:
        MissingRequirementsFileError: If the specified requirements file does not exist or cannot be accessed.
        ModuleInstallationError: If an error occurs during the module installation using pip.
        DependencyError: If an OS-level error occurs during the installation process.
    """
    
    absolute_path = os.path.abspath(path)
    logger = logging.getLogger(logger)
    
    # Check if the file exists and is valid
    if not os.path.isfile(absolute_path):
        raise MissingRequirementsFileError(logger.error(f"The {path} file was not found."))
    
    try:
        # Preloading existing packages to avoid installing duplicates
        existing_packages = get_installed_packages(logger)
        
        with open(absolute_path, "r", encoding="utf-8") as file:
            required_packages = [line.strip() for line in file.readline() if line.strip()]
        
        # Filter packages that require installation
        packages_to_install = [
            package for package in required_packages if not is_package_installed(package, existing_packages)
        ]
        
        if not packages_to_install:
            logger.info("All dependencies are already installed.")
            
        # Build pip command
        command = [
            sys.executable, "-m", "pip", "install", "--no-cache-dir", "--no-deps",
            *packages_to_install
        ]
        
        result = subprocess.run(
            command,
            check=True,  # Raises CalledProcessError if the command fails
            capture_output=True,  # Captures stdout and stderr for debugging/logging
            text=True  # Decodes stdout/stderr as text
        )
        
        logger.info("Successfully installed dependencies.")
        logger.debug("Command output:\n%s", result.stdout)
    
    except subprocess.CalledProcessError as error:
        raise ModuleInstallationError(logger.error(f"An error occurred while installing dependencies:\n{error.stderr or 'Unknown error'}")) from error
    except OSError as os_error:
        raise DependencyError(logger.error(f"OS error occurred during installation: {os_error}")) from os_error
    

def install_modules(module: str, version: str = None, version_range: str = None, logger: str = "main") -> bool:
    """install_modules Install a specified Python module with optional version, version range, and logging.

    This function allows for installing a Python module from PyPI, with the option to specify a specific version, version range, or using the latest available version. 
    It supports logging for debugging purposes and handles various error scenarios like dependency issues or installation failure.

    Arguments:
        module {str} -- The name of the module to be installed.

    Keyword Arguments:
        version {str} -- The specific version of the module to be installed. Defaults to None. (default: {None})
        version_range {str} -- A version range specifier if a specific range of versions is needed. (default: {None})
        logger {str} -- Choose the logger used (default: {"main"})

    Raises:
        ModuleInstallationError: Raised when the module installation fails due to system issues, dependency issues, or other reasons.
        ModuleInstallationError: Raised when the requested version or version range is incompatible or not available on PyPI.

    Returns:
        bool -- True if the module was installed successfully.
    """
    
    # Format the package with a version or version range
    if version:
        package_specifier = f"{module}=={version}"
    elif version_range:
        package_specifier = f"{module}{version_range}"  # e.g. "module>=1.2.0, !=2.0.0"
    else:
        package_specifier = module  # Latest version installed by default
        
    try:

        # Pip command with specifier
        command = [
            sys.executable, "-m", "pip", "install", package_specifier
        ]

        # Call pip install
        result = subprocess.run(
            command,
            check=True,  # Raises CalledProcessError if the command fails
            capture_output=True,  # Captures stdout and stderr for debugging/logging
            text=True  # Decodes stdout/stderr as text
        )

        logger.info(f"Module {module} successfully installed.")
        logger.debug("Command output:\n%s", result.stdout)

    except subprocess.CalledProcessError as error:
        raise ModuleInstallationError(logger.error(f"An error occurred while installing the module {module}:\n{error.stderr or 'Unknown error'}")) from error
    except (OSError, DependencyError) as dep_error:
        raise ModuleInstallationError(logger.error(f"System or dependency error for the module {module}: {dep_error}")) from dep_error
    
    return True
