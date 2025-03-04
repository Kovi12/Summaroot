import logging
import subprocess

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def run_script(script_name):
    try:
        logging.info(f"Starting {script_name}...")
        subprocess.run(["python", script_name], check=True)
        logging.info(f"Finished {script_name}.")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error executing {script_name}: {e}")

def main():
    """Main function to run all steps in order."""
    logging.info("=== Starting Pipeline ===")

    # Step 1: Process PDFs (OCR + Extract Text)
    run_script("step1.py")

    # Step 2: Compute Similarities & Generate metadata.json
    run_script("step2.py")

    # Step 3: Highlight Text in PDFs
    run_script("step3.py")

    logging.info("=== Pipeline Completed Successfully ===")

if __name__ == "__main__":
    main()
