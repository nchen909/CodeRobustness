
import re

def extract_data_from_file(file_path):
    data = {}
    with open(file_path, "r") as file:
        lines = file.readlines()
        for line in lines:
            line = re.sub(r'\d{2}/\d{2}/\d{4} \d{2}:\d{2}:\d{2} - INFO - __main__ -  ', '', line)
            if "args.model_name" in line:
                model_name = line.strip().split(":")[-1].strip()
                if model_name not in data:
                    data[model_name] = {}
            elif "args.task" in line:
                task = line.strip().split(":")[-1].strip()
                if task not in data[model_name]:
                    data[model_name][task] = {}
            elif "args.sub_task" in line:
                sub_task = line.strip().split(":")[-1].strip()
                if sub_task not in data[model_name][task]:
                    data[model_name][task][sub_task] = {}
            elif re.search(r'\[best-(acc|f1|bleu|ppl)\]', line):
                key = re.search(r'\[best-(acc|f1|bleu|ppl)\]', line).group(1)
                values = re.findall(r'([\w-]+)[\s=:]+([\d\.]+)', line)
                data[model_name][task][sub_task][key] = {k: float(v) for k, v in values}

    return data

def fill_markdown_table(data):
#     header = """|   attack_bfs  |   clone   |        |       | defect |      java-cs     |     | cs-java |    | ruby | js   | go   | python | java | php            |
# |:-------------:|:---------:|:------:|:-----:|--------|:----------------:|:---:|:-------:|:--:|------|------|------|--------|------|----------------|
# |               | precision | recall | f1    | acc    | bleu             | em  | bleu    | em | bleu | bleu | bleu | bleu   | bleu | bleu           |
# """
    header = """|   textual_attack_funcname  | defect |   clone   |        |    | ruby | js   | go   | python | java | php  | java-cs |    | cs-java |    |
|:-------------:|--------|:---------:|:------:|----|------|------|------|--------|------|------|:-------:|:--:|:-------:|----|
|               | acc    | precision | recall | f1 | bleu | bleu | bleu | bleu   | bleu | bleu | bleu    | em | bleu    | em |
"""
    models = ["graphcodebert","plbart", "codet5","unixcoder"]

    table = header

    for model in models:
        model_data = data.get(model, {})
        row = f"| {model} "
        for task, metrics in model_data.items():
            for sub_task, values in metrics.items():
                if values=={}:
                    row += "| "
                elif task == "clone" and sub_task == "":
                    row += f"| {round(values['f1']['precision'], 2)} | {round(values['f1']['recall'], 2)} | {round(values['f1']['test-f1'], 2)} "
                elif task == "defect" and sub_task == "":
                    row += f"| {round(values['acc']['test_acc'], 2)} "
                elif task == "translate" and sub_task in ["java-cs", "cs-java"]:
                    if ("bleu" not in values) or ("ppl" not in values):
                        row += f"|  |  "
                        print("error in:", model, task, sub_task)
                        continue
                    bleu_values = values["bleu"]
                    ppl_values = values["ppl"]
                    if bleu_values["bleu-4"] >= ppl_values["bleu-4"]:
                        row += f"| {bleu_values['bleu-4']} (best-bleu) | {round(bleu_values['em'], 1)} "
                    else:
                        row += f"| {ppl_values['bleu-4']} (best-ppl) | {round(ppl_values['em'], 1)} "
                elif task == "summarize" and sub_task in ["php",'python','ruby','javascript','go','java']:
                    if ("bleu" not in values) or ("ppl" not in values):
                        row += f"|  |  "
                        print("error in:", model, task, sub_task)
                        continue
                    bleu_values = values["bleu"]
                    ppl_values = values["ppl"]
                    if bleu_values["bleu-4"] >= ppl_values["bleu-4"]:
                        row += f"| {bleu_values['bleu-4']} (best-bleu) "
                    else:
                        row += f"| {ppl_values['bleu-4']} (best-ppl) "
                else:
                    row += "| "
        table += row + "|\n"

    return table


file_path = "/root/autodl-tmp/HugCode/log_bfs2dfs/bfs2dfs.txt"
data = extract_data_from_file(file_path)
markdown_table = fill_markdown_table(data)
print(markdown_table)
