from transformers import RobertaTokenizer, T5ForConditionalGeneration

if __name__ == '__main__':
    tokenizer = RobertaTokenizer.from_pretrained('Salesforce/codet5-base')
    model = T5ForConditionalGeneration.from_pretrained('Salesforce/codet5-base-multi-sum')

    text = """def max(a, b):
    x = b if b > a else a
    return x"""

    bfsattack = """: max def ) b , a ( x return = x a else if b a > b
    """
    dfsattack = """x return a else a > b if b = x : ) b , a ( max def
    """
    subtree_attack= """def max ( a , b ) : x = b if b > a else a
    """
    funcnameattack="""def sum(a, b):
    x = b if b > a else a
    return x"""

    # finetunepredictions= "Returns the maximum of two tokens."
    # bfspredictions="Return the maximum value of a function."
    # dfspredictions="max function."
    # subtreepredictions="Returns the maximum of two numbers."
    # funcnamepredictions="Sum of two terms."
    # gold_fn="Returns the maximum of two integers."
    input_ids = tokenizer(bfsattack, return_tensors="pt").input_ids

    generated_ids = model.generate(input_ids, max_length=20)
    print(tokenizer.decode(generated_ids[0], skip_special_tokens=True))
    # this prints: "Convert a SVG string to a QImage."