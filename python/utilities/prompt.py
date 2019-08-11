def prompt(vals:tuple, prompts:dict, generators:dict):

    result = {}
    
    for val in vals:
        print(prompts[val])
        cmd = input('\033[92m fopd:\033[00m ')

        if val in generators:
            # look for invocation of custom generators by user (e.g. they entered 'auto')
            if cmd.lower() in generators[val]:
                result[val] = generators[val][cmd.lower()](cmd.lower())
            # look for a default value generator
            elif 'default' in generators[val]: 
                result[val] = generators[val]['default'](cmd)
            else:
                result[val] = cmd
        else:
            result[val] = cmd

    return result 
