#!/usr/bin/env python3

import re
import argparse
import os


in_file = "./cassette_shuffle/cassette.fa"
min_flank = 10
pept_len = [8,9,10,11]

def main():
    input_parser = argparse.ArgumentParser(description='CaShuff: the program for generation of the shuffled peptide junctions.')
    input_parser.add_argument('f', metavar='input_file.fa', help='FASTA file of peptides with flanks; the fasta header format: >name (beg_pept_pos..end_pept_pos)')
    input_parser.add_argument('-l', metavar='PEPTIE_LENGTH', nargs='+', type=int, default=[8,9,10,11], help='lengths of peptides', required=False)
    input_parser.add_argument('-m', metavar='MIN_FLANKS_LENGTH', type=float, default=10, help='min length of flanks', required=False)
    
    args = input_parser.parse_args()
    in_file = args.f
    pept_len = args.l
    min_flank = args.m
    
    fasta = FastaParser(in_file)
    output = Output()
    comb = Combinator()
    for item in fasta.get():
        if len(item["seq"]) == 1:
            comb.append(item, 1, 0)
        elif re.search("\*$", item["seq"]):
            comb.append(item, 0, 1)
        else:
            comb.append(item, 0, 0)
    junctions = JunctionPept()
    for combination in comb.get():
        seq_1, end_1 = combination[0]["seq"], combination[0]["end"]
        seq_2, beg_2 = combination[1]["seq"], combination[1]["beg"]
        if len(seq_1) == 1: # START
            end_1 = 0
        for peptide in junctions.get(seq_1, end_1, seq_2, beg_2, min_flank, pept_len):
            header = ">{}_{}_{}_{}_{}_{}".format(
                combination[0]["name"],
                combination[1]["name"],
                peptide["l_flank_pos"],
                peptide["l_insert_pos"],
                peptide["r_insert_pos"],
                peptide["r_flank_pos"])
            peptide = peptide["pept"]
            output.print2fasta(header, peptide)
            print(header)
            print(peptide)
    output.close()
# end of main()

class Output:
    def __init__(self, dir_name='.'):
        dir_name = re.sub("\/$", "", dir_name)
        self._dname = dir_name
        self._out = {}
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
    
    def print2fasta(self, header, peptide):
        plen = len(peptide)
        fname = self._dname + "/" + "peptides." + str(plen) + ".fa"
        if plen not in self._out:
            self._out[plen] = open(fname, "w")
        self._out[plen].write(header + "\n" + peptide + "\n")
    
    def close(self):
        for f in self._out.values():
            f.close()
# end of class Output

class FastaParser:
    def __init__(self, file_name):
        self._fasta = {}
        with open(file_name, "r") as infile:
            header = ""
            for line in infile:
                line = line.strip()
                h_pattern = re.match(">(\S+)\D+(\d+)\.\.(\d+)", line)
                if h_pattern:
                    header = h_pattern.group(1)
                    self._fasta[header] = {"name": header, "beg": int(h_pattern.group(2)), "end": int(h_pattern.group(3)), "seq": ""}
                elif header:
                    self._fasta[header]["seq"] += re.sub("[^A-Za-z*]", "", line)
                else:
                    raise ValueError('Wrong FASTA format!')
    def get(self):
        return self._fasta.values()
# end of class FastaParser

class Combinator:
    def __init__(self):
        self._array = []
    
    def append(self, item, beg=0, end=0):
        self._array.append({"item": item, "beg": beg, "end": end})
        
    def get(self):
        comb = []
        for i, item_i in enumerate(self._array):
            for j, item_j in enumerate(self._array):
                if i == j:
                    next
                else:
                    if not item_i["end"] and not item_j["beg"]:
                        if len(comb) > 2 and item_i["beg"] and item_j["end"]:
                            next
                        else:
                            comb.append([item_i["item"], item_j["item"]])
        return comb
# end of class Combinator

class JunctionPept:
    def __init__(self):
        pass
    
    def get(self, l_seq, l_pos, r_seq, r_pos, mflank, p_len):
        if(l_seq == r_seq):
            raise ValueError('Wrong combination:\n{}\n{}\n'.format(l_seq, r_seq))
        
        peptides = []
        rng_start = l_pos + mflank
        rng_end = len(l_seq) + 1
        if rng_start >= rng_end:
            rng_start = rng_end - 1
        for l in range(rng_start, rng_end):
            l_flank = l_seq[:l]
            shift = len(l_flank) - (l_pos + mflank)
            if shift < 0:
                shift = 0
            for r in range(shift, r_pos - mflank):
                r_flank = r_seq[r:]
                for plen in p_len:
                    for p_pos in range(1, plen):
                        pept = l_flank[-p_pos:]
                        l_ppos = len(pept)
                        tmp_flank = r_flank[:plen-p_pos]
                        pept += tmp_flank
                        if len(pept) < plen:
                            break
                        r_ppos = len(pept) - len(tmp_flank) + 1
                        peptides.append({"pept": pept, "l_flank": l_flank, "r_flank": r_flank, "l_flank_pos": l, "r_flank_pos": r + 1, "l_insert_pos": l_ppos, "r_insert_pos": r_ppos})
        return peptides
# end of class JunctionPept

if __name__ == '__main__':
    main()
