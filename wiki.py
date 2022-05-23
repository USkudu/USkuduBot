import wikipedia
import re


wikipedia.set_lang("ru")


def wiki(key_word):
    try:
        data = wikipedia.page(key_word)
        wikitext = data.content[:1000]
        wik = wikitext.split('.')
        wik = wik[:-1]
        result = ''
        for x in wik:
            if '==' not in x:
                if len((x.strip())) > 3:
                    result = result + x + '.'
            else:
                break
        result = re.sub(r'\([^()]*\)', '', result)
        result = re.sub(r'\{[^\{\}]*\}', '', result)
        return result
    except Exception:
        return 'В энциклопедии нет информации об этом.'
