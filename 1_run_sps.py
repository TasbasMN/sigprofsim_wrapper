import argparse
import os
import shutil
from datetime import datetime
from SigProfilerSimulator import SigProfilerSimulator as sigSim
import re
import pandas as pd
import glob

def backup_and_remove_non_vcf(project_folder):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder = f"backups/{os.path.basename(project_folder)}_backup_{timestamp}"
    
    os.makedirs(backup_folder, exist_ok=True)
    
    for item in os.listdir(project_folder):
        source = os.path.join(project_folder, item)
        destination = os.path.join(backup_folder, item)
        
        if os.path.isfile(source):
            if not source.endswith('.vcf'):
                shutil.copy2(source, destination)
                os.remove(source)
                print(f"Backed up and removed file: {item}")
        elif os.path.isdir(source):
            shutil.copytree(source, destination)
            shutil.rmtree(source)
            print(f"Backed up and removed directory: {item}")
    
    print(f"Backup completed and non-VCF items removed. Backup folder: {backup_folder}")

def vcf_to_bed(vcf_file, bed_file, cushion=1):
    with open(vcf_file, 'r') as vcf, open(bed_file, 'w') as bed:
        for line in vcf:
            if line.startswith('#'):
                continue  # Skip header lines
            
            fields = line.strip().split('\t')
            
            chrom = fields[0]
            pos = int(fields[1])
            
            # Create a region around the mutation position
            start = max(0, pos - 1 - cushion)  # Ensure start is not negative
            end = pos + cushion
            
            # Write to BED file
            bed.write(f"{chrom}\t{start}\t{end}\n")

    print(f"Conversion complete. BED file saved as {bed_file}")




def main():
    parser = argparse.ArgumentParser(description="VCF to BED converter and SigProfilerSimulator runner")
    parser.add_argument("project_folder", help="Path to the project folder containing VCF files")
    parser.add_argument("--bed_file", default=None, help="Path to the input BED file")
    parser.add_argument("--simulations", type=int, default=1, help="Number of simulations to run")
    parser.add_argument("--poisson", action="store_true", help="Use Poisson noise")
    parser.add_argument("--genome_build", default="GRCh37")
    
    args = parser.parse_args()
    
    # check if project folder exists
    if not os.path.exists(args.project_folder):
        print(f"Project folder {args.project_folder} does not exist, creating")
        os.makedirs(args.project_folder)
    

    # Backup non-VCF files and remove them from the project folder
    backup_and_remove_non_vcf(args.project_folder)


    # Find the first VCF file for gender determination
    vcf_file = next((os.path.join(args.project_folder, f) for f in os.listdir(args.project_folder) if f.endswith('.vcf')), None)

    if vcf_file is None:
        print(f"No VCF file found in {args.project_folder}")
        return

    # Only create and use BED file if explicitly provided
    if args.bed_file:
        vcf_to_bed(vcf_file, args.bed_file)
        bed_file_arg = {"bed_file": args.bed_file}
    else:
        bed_file_arg = {}

    sigSim.SigProfilerSimulator(
        args.project_folder,
        args.project_folder,
        args.genome_build,
        contexts=["96"],
        # gender=determine_gender(vcf_file),
        simulations=args.simulations,
        vcf=True,
        # noisePoisson=args.poisson,
        chrom_based=True,
        **bed_file_arg
    )
    
    # remove input folder inside project dir
    shutil.rmtree(os.path.join(args.project_folder, "input"))
    
    # zip logs folder and move to project root
    shutil.make_archive(os.path.join(args.project_folder, f"{args.project_folder}"), 'zip', os.path.join(args.project_folder, "logs"))
    shutil.rmtree(os.path.join(args.project_folder, "logs"))
    
    # rename log zip file
    os.rename(os.path.join(args.project_folder, f"{args.project_folder}.zip"), os.path.join(args.project_folder, f"{args.project_folder}_logs.zip"))
    
    
    # remove preciously copied vcf files from the project folder
    for item in os.listdir(args.project_folder):
        if item.endswith('.vcf'):
            os.remove(os.path.join(args.project_folder, item))
            
    # remove output/DBS folder
    shutil.rmtree(os.path.join(args.project_folder, "output", "DBS"))
    shutil.rmtree(os.path.join(args.project_folder, "output", "SBS"))
    shutil.rmtree(os.path.join(args.project_folder, "output", "vcf_files"))
    
    # Find all VCF files in the directory tree
    simulations_path = os.path.join(args.project_folder, "output", "simulations")
    vcf_files = glob.glob(os.path.join(simulations_path, "**", "*.vcf"), recursive=True)

    for source in vcf_files:
        file = os.path.basename(source)
        
        # Remove suffix and add "+"
        new_filename = re.sub(r'_[^_]+\.vcf$', '+.vcf', file)
        
        destination = os.path.join(args.project_folder, new_filename)
        
        # If the destination file already exists, append a number
        counter = 1
        while os.path.exists(destination):
            base, ext = os.path.splitext(new_filename)
            destination = os.path.join(args.project_folder, f"{base}_{counter}{ext}")
            counter += 1
        
        shutil.move(source, destination)

        # Open the moved file, delete unwanted columns, and overwrite
        df = pd.read_csv(destination, sep='\t', comment='#', usecols=range(5), header=None, low_memory=False)
        df.to_csv(destination, sep='\t', index=False, header=False)
                        
    
    # remove output folder
    shutil.rmtree(os.path.join(args.project_folder, "output"))


    

if __name__ == "__main__":
    main()
