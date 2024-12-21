def merge_dicts(dict1, dict2):
    merged_dict = dict1.copy()  # Crée une copie de dict1 pour ne pas modifier l'original

    for key, value in dict2.items():
        if key in merged_dict:
            # Si la clé existe déjà, on fusionne les valeurs
            if isinstance(merged_dict[key], list):
                merged_dict[key] += value
            else:
                merged_dict[key] = [merged_dict[key], value]  # On met les valeurs dans une liste
        else:
            merged_dict[key] = [value]

    return merged_dict
