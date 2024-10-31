# GSP Toolkit

The **GSP Toolkit** is a Python package that implements the Generalized Sequential Pattern (GSP) algorithm. Originally developed as part of the Course Sequencing Analysis Tool (CSAT) to analyze and sequence student course data, the toolkit has been extended to support more general use cases. It is designed for applications where analyzing sequential patterns is essential, such as course sequencing or other data patterns.

The package supports grouping items based on a specified granularity using concurrency and provides both a command-line interface (CLI) and a graphical user interface (GUI).

## Features

- **GSP Algorithm**: Analyze sequential patterns using the Generalized Sequential Pattern (GSP) algorithm.
- **Granularity-Based Grouping**: Use concurrency to group items by a specified time granularity, such as semesters (quarters) or months.
- **Command-Line Interface (CLI)**: Run the GSP algorithm from the terminal for efficient scripting and automation.
- **Graphical User Interface (GUI)**: Easily configure and run the algorithm using an interactive graphical interface.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Fordham-EDM-Lab/course-sequencing-analysis-tool.git
   ```

2. Navigate to the project directory:
   ```bash
   cd course-sequencing-analysis-tool
   ```

3. Install the package:
   ```bash
   pip install .
   ```

## Usage

### Command-Line Interface (CLI)

You can run the GSP algorithm using the CLI. Here’s an example:

```bash
gsp-cli -i data.csv -s 50,100 -c BIO,CHEM --mode separate -o results --concurrency
```

For more detailed instructions and examples, please refer to the [GSP Toolkit Manual](https://docs.google.com/document/d/1yb6dg26jO_m0ir80vgfoN9ED0RF3bohMhJi0B3aig8w/edit?usp=sharing).

### Graphical User Interface (GUI)

Launch the GUI for an easy-to-use interface:

```bash
gsp-gui
```

The GUI allows you to:
- Load your data file.
- Set support thresholds and categories.
- Group items based on granularity (e.g., semester or month).

## Requirements

- Python 3.10 or later
- Dependencies are automatically installed when you run `pip install .`.

## Data Requirements

To understand the required data format, refer to the [Data Dictionary](https://docs.google.com/spreadsheets/d/19fIA5eiZxCav0MiElDoTDvuyinyYroxuJF9LWmQxvNc/edit?usp=sharing).

### Example Datasets

Example datasets for testing and exploring the GSP Toolkit are available [here on Google Drive](https://drive.google.com/drive/folders/1hyjKf69IY1wbkWwSl0AzG-wJTITOXlIW?usp=sharing).

## Development Roadmap

- **Current**: Working on robust testing and validation to implement the general case for sequential pattern analysis, beyond just course sequencing. Focused on ensuring the toolkit handles various data scenarios effectively.
- **Future**: Finalize packaging and prepare the toolkit for distribution on PyPi (Python Package Index). Additionally, explore ways to optimize the GSP algorithm, such as implementing parallel execution, to improve performance for large datasets.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
