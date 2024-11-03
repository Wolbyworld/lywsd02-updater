# LYWSD02 Updater

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Screenshots](#screenshots)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Overview

**LYWSD02 Updater** is a Python-based desktop application designed to synchronize the current time and configure temperature units on your LYWSD02 Bluetooth device. Leveraging Bluetooth Low Energy (BLE) communication, the application offers a user-friendly graphical interface built with Tkinter, enabling seamless device scanning, selection, and configuration.

## Features

- **Bluetooth Scanning:**
  - Perform quick scans for Bluetooth devices.
  - Initiate continuous scanning until manually stopped.
  - Categorize detected devices into LYWSD02 and other Bluetooth devices.

- **Device Management:**
  - Search and filter through detected Bluetooth devices.
  - Select and manage multiple devices with ease.

- **Time Synchronization:**
  - Set UTC offset with support for fractional hours (e.g., UTC+05:30).
  - Optional 30-minute offset for precise time adjustments.
  - Real-time display of the current time adjusted to the selected time zone.

- **Temperature Unit Configuration:**
  - Choose between Celsius (°C) and Fahrenheit (°F) units.

- **User-Friendly Interface:**
  - Comprehensive console log for monitoring scanning and updating processes.
  - Detailed instructions accessible within the application.

- **Error Handling:**
  - Validates user inputs for time zone to prevent incorrect configurations.
  - Provides informative messages for successful updates and encountered errors.

## Prerequisites

Before installing and running the application, ensure that your system meets the following requirements:

- **Operating System:** Windows, macOS, or Linux
- **Python Version:** Python 3.7 or higher
- **Bluetooth Adapter:** Required for Bluetooth communication with LYWSD02 devices

## Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/Wolbyworld/lywsd02-updater.git
   cd lywsd02-updater
   ```

2. **Create a Virtual Environment (Optional but Recommended)**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   **Note:** If `requirements.txt` is not provided, you can install the necessary packages individually:

   ```bash
   pip install bleak
   ```

   - `bleak`: For Bluetooth Low Energy (BLE) communication.
   - `tkinter`: Typically included with Python installations. If not, install it via your system's package manager.

4. **Run the Application**

   ```bash
   python lywsd02_updater.py
   ```

## Usage

1. **Launch the Application**

   After running the script, the LYWSD02 Updater window will appear.

2. **Scan for Devices**

   - **Scan for 10 Seconds:** Click this button to perform a quick scan for Bluetooth devices for a duration of 10 seconds.
   - **Start Continuous Scan:** Click to continuously scan for Bluetooth devices until you manually stop the scan.
   - **Stop Scanning:** Click to halt an ongoing scan.

3. **Select Your LYWSD02 Device**

   - Detected LYWSD02 devices will appear under the "LYWSD02 Devices" section.
   - Select your desired device from the list.

4. **Configure Time Settings**

   - **Time Zone (UTC Offset):** Enter your UTC offset in hours (e.g., `+5` for UTC+5).
   - **Add 30-Minute Offset:** If your time zone includes a 30-minute difference (e.g., UTC+5:30), check this box.

5. **Select Temperature Unit**

   - Choose between **Celsius (C)** and **Fahrenheit (F)** based on your preference.

6. **Update Device**

   - Click the "Update Device" button to synchronize the time and update the temperature unit on your LYWSD02 device.
   - Monitor the "Console" section for real-time logs and status updates.

7. **View Current Time**

   - The "Current Time" label displays the adjusted current time based on your selected time zone and offset.

8. **Access Instructions**

   - Click the "Instructions" hyperlink to view detailed usage guidelines within the application.

## Configuration

- **Time Zone Entry:**
  - Enter integer values between `-12` and `+14` to represent UTC offsets.
  - For time zones with a 30-minute difference, use the "Add 30-Minute Offset" checkbox.

- **Temperature Unit:**
  - Select **Celsius (C)** or **Fahrenheit (F)** to set your preferred temperature unit on the device.

## Screenshots

*Screenshots are currently not available. Future updates may include visual aids to enhance user understanding.*

## Troubleshooting

- **Bluetooth Not Detected:**
  - Ensure your Bluetooth adapter is properly connected and enabled.
  - Verify that your system's Bluetooth drivers are up to date.

- **No Devices Found:**
  - Make sure your LYWSD02 device is powered on and within range.
  - Restart the scanning process.

- **Connection Errors:**
  - If the application fails to connect to the device, try restarting both the application and your LYWSD02 device.
  - Ensure no other application is currently connected to the LYWSD02 device.

- **Invalid UTC Offset:**
  - Ensure that the UTC offset entered is within the range of `-12` to `+14`.
  - If your time zone includes a 30-minute offset, check the corresponding box.

- **Application Crashes or Freezes:**
  - Ensure you are using a compatible Python version (3.7 or higher).
  - Check if all dependencies are correctly installed.
  - Refer to the console logs for specific error messages.

## Contributing

Contributions are welcome! Whether it's improving the code, enhancing the documentation, or suggesting new features, your input is valuable.

1. **Fork the Repository**

2. **Create a New Branch**

   ```bash
   git checkout -b feature/YourFeatureName
   ```

3. **Commit Your Changes**

   ```bash
   git commit -m "Add Your Feature"
   ```

4. **Push to the Branch**

   ```bash
   git push origin feature/YourFeatureName
   ```

5. **Open a Pull Request**

Please ensure that your contributions adhere to the project's coding standards and include appropriate tests and documentation where necessary.

## License

This project is licensed under the [MIT License](LICENSE).

