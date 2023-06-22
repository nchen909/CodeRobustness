import sys
sys.path.append("/root/autodl-tmp/HugCode")
from evaluator.smooth_bleu import bleu
import re
def splitPuncts(line):
    return ' '.join(re.findall(r"[\w]+|[^\s\w]", line))
def computeMaps(predictions, gold_fn):
    predictionMap = {}
    goldMap = {}
    # gf = open(goldfile, 'r',encoding='utf-8')

    predictionMap[0] = [splitPuncts(predictions.strip().lower())]

    # for row in gf:
    #     (rid, pred) = row.split('\t')
    #     if rid in predictionMap:  # Only insert if the id exists for the method
    #         if rid not in goldMap:
    #             goldMap[rid] = []
    goldMap[0]=[splitPuncts(gold_fn.strip().lower())]

    # sys.stderr.write('Total: ' + str(len(goldMap)) + '\n')
    return (goldMap, predictionMap)

# m1 is the reference map
# m2 is the prediction map
def bleuFromMaps(m1, m2):
    score = [0] * 5
    num = 0.0

    for key in m1:
        if key in m2:
            # print(m1[key], m2[key][0])
            bl = bleu(m1[key], m2[key][0])
            score = [score[i] + bl[i] for i in range(0, len(bl))]
            num += 1
    return [s * 100.0 / num for s in score]

if __name__ == "__main__":
    finetunepredictions= "Returns the maximum of two tokens."
    bfspredictions="Returns the maximum value of a function."#"Return the maximum value of a function."
    dfspredictions="max function."
    subtreepredictions="Return the maximum of two numbers."
    funcnamepredictions="Sum of two terms."
    gold_fn="Returns the maximum of two integers."
    (goldMap, predictionMap) = computeMaps(bfspredictions, gold_fn)
    bleu4 = round(bleuFromMaps(
        goldMap, predictionMap)[0], 2)
    print(bleu4)