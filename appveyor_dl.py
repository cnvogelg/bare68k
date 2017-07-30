#!/usr/bin/env python
# appveyor artifacts download script

from __future__ import print_function

import requests
import os


def appveyor_download(user, project, branch):
    api_url = 'https://ci.appveyor.com/api'
    prj_url = '{}/projects/{}/{}/branch/{}'.format(
        api_url, user, project, branch)

    # get project info
    r = requests.get(prj_url)
    if r.status_code != 200:
        raise IOError("ERROR getting project URL '{}'".format(prj_url))
    prj_info = r.json()

    # get artifacts
    jobs = prj_info['build']['jobs']
    for job in jobs:
        job_id = job['jobId']
        # get job info
        artf_url = '{}/buildjobs/{}/artifacts'.format(api_url, job_id)
        r = requests.get(artf_url)
        if r.status_code != 200:
            raise IOError("ERROR getting artifact URL '{}'".format(artf_url))
        artf_info = r.json()
        for artf in artf_info:
            fileName = artf['fileName']
            size = artf['size']
            file_url = '{}/buildjobs/{}/artifacts/{}'.format(
                api_url, job_id, fileName)
            r = requests.get(file_url)
            if r.status_code != 200:
                raise IOError("ERROR getting file URL '{}'".format(file_url))
            # ensure local dir
            dirName = os.path.dirname(fileName)
            if dirName != "":
                if not os.path.isdir(dirName):
                    print("creating dir:", dirName)
                    os.makedirs(dirName)
            print("downloading:", fileName, size)
            # copy file
            with open(fileName, 'wb') as f:
                for chunk in r:
                    f.write(chunk)
            # check size
            if os.path.getsize(fileName) != size:
                raise IOError(
                    "ERROR invalid file size: {} {}".format(fileName, size))
