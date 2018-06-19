#!/usr/bin/python3
import os
import sys
import re
from shutil import copyfile
from pathlib import Path
import ruamel.yaml

stack_file = os.getenv("DEST_FILE", "/dist/docker-compose.yml")
env_file = os.getenv("DEST_ENV_FILE", "/dist/.env")
source_stack_file = os.getenv("SRC_FILE", "/src/docker-compose.yml")
source_env_file = os.getenv("SRC_ENV_FILE", "/src/.env")


# create docker-compose.yml if not exist
def set_file(src, dest):
    my_file = Path(dest)
    if not my_file.is_file():
        copyfile(src, dest)
        print(f"{dest} created")
    os.chmod(dest, 0o777)


# load docker-compose.yml
def load_stack(stack_file):
    f = open(stack_file, "r")
    data = f.read()
    f.close()
    return ruamel.yaml.load(data, ruamel.yaml.RoundTripLoader)


def find_commented_services(code):
    commented_services = {}
    commented_service = None
    try:
        for i in code._yaml_comment.items.keys():
            for comment_style in code._yaml_comment.items[i]:
                if not comment_style:
                    continue
                for comment in comment_style:
                    r = re.search(r'^[#]{1,}  (\w.*):$', comment.value)
                    if r:
                        commented_service = r.group(1)
                        commented_services[commented_service] = []
                    else:
                        if commented_service:
                            commented_services[commented_service].append(comment)
    except:
        pass
    return commented_services


def check_yml(source_stack_file, stack_file, source_env_file, env_file):
    set_file(source_env_file, env_file)
    set_file(source_stack_file, stack_file)
    src_code = load_stack(source_stack_file)
    dest_code = load_stack(stack_file)
    if 'services' not in dest_code.keys():
        print('''
        ------------------------------------
        You stack is empty! I\'m reload him!
        ------------------------------------
        ''')
        os.remove(stack_file)
        set_file(source_stack_file, stack_file)
        dest_code = load_stack(stack_file)
    # add new service
    # find comment services by user
    src_commented_services = find_commented_services(src_code)
    src_commented_services.update(find_commented_services(src_code['services']))
    dest_commented_services = find_commented_services(dest_code)
    dest_commented_services.update(find_commented_services(dest_code['services']))

    new_services = {k: src_code['services'][k] for k in set(src_code['services']) - set(dest_code['services'])}
    if new_services:
        for service in new_services.keys():
            if service not in dest_commented_services.keys():
                dest_code['services'].update({service: new_services[service]})
                print(f'''                  ==================> New Service '{service}' ''')
            else:
                print(f'''                  ==================> Service '{service}' was update in repo (if you need in update in this service remove this from docker-compose.yml and restart)''')
    not_in_repo_services = {k: dest_code['services'][k] for k in set(dest_code['services']) - set(src_code['services'])}
    if not_in_repo_services:
        for service in not_in_repo_services.keys():
            if service not in src_commented_services.keys():
                print(f'''                  ==================> The '{service}' service is not needed (if you dont need in this service, remove this from docker-compose.yml and restart)''')
    return dest_code


dest_code = check_yml(source_stack_file, stack_file, source_env_file, env_file)
with open(stack_file, 'w') as _f:
    os.chmod(stack_file, 0o777)
    ruamel.yaml.dump(
        dest_code,
        stream=_f,
        Dumper=ruamel.yaml.RoundTripDumper,
        explicit_start=True,
        width=1024
    )
