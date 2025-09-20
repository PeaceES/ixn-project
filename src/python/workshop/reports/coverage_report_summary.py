import xml.etree.ElementTree as ET
from pathlib import Path

def parse_coverage_xml(xml_path):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    
    # Overall line-rate
    overall_line_rate = float(root.attrib.get('line-rate', 0))
    print(f"\nOverall Line Coverage: {overall_line_rate * 100:.2f}%\n")

    print("Per-file coverage:")
    print("------------------")
    files = []
    for package in root.findall('.//package'):
        for clazz in package.findall('classes/class'):
            filename = clazz.attrib.get('filename')
            line_rate = float(clazz.attrib.get('line-rate', 0))
            files.append((filename, line_rate))
            print(f"{filename:50} {line_rate * 100:6.2f}%")

    # Show files with lowest coverage
    print("\nFiles with lowest coverage:")
    print("--------------------------")
    for filename, line_rate in sorted(files, key=lambda x: x[1])[:5]:
        print(f"{filename:50} {line_rate * 100:6.2f}%")

    # Optionally, list missed lines for each file
    missed_lines = {}
    for package in root.findall('.//package'):
        for clazz in package.findall('classes/class'):
            filename = clazz.attrib.get('filename')
            missed = []
            for line in clazz.findall('lines/line'):
                if int(line.attrib.get('hits', 1)) == 0:
                    missed.append(line.attrib.get('number'))
            if missed:
                missed_lines[filename] = missed
    if missed_lines:
        print("\nMissed lines per file:")
        print("---------------------")
        for filename, lines in missed_lines.items():
            print(f"{filename}: {', '.join(lines)}")

if __name__ == "__main__":
    xml_path = Path(__file__).parent / "coverage_integration.xml"
    if not xml_path.exists():
        print(f"Coverage XML not found at {xml_path}")
    else:
        parse_coverage_xml(xml_path)
