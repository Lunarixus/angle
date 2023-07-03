#!/usr/bin/env vpython3
# Copyright 2021 The ANGLE Project Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""Script to generate the test spec JSON files. Calls Chromium's generate_buildbot_json.

=== NOTE: DO NOT RUN THIS SCRIPT DIRECTLY. ===
Run scripts/run_code_generation.py instead to update necessary hashes.

"""

import os
import pprint
import sys
import subprocess
import tempfile

d = os.path.dirname
THIS_DIR = d(os.path.abspath(__file__))
TESTING_BBOT_DIR = os.path.join(d(d(THIS_DIR)), 'testing', 'buildbot')
sys.path.insert(0, TESTING_BBOT_DIR)

import generate_buildbot_json

# Add custom mixins here.
ADDITIONAL_MIXINS = {
    'angle_skia_gold_test': {
        'args': [
            '--git-revision=${got_angle_revision}',
            # BREAK GLASS IN CASE OF EMERGENCY
            # Uncommenting this argument will bypass all interactions with Skia
            # Gold in any tests that use it. This is meant as a temporary
            # emergency stop in case of a Gold outage that's affecting the bots.
            # '--bypass-skia-gold-functionality',
        ],
        'precommit_args': [
            '--gerrit-issue=${patch_issue}',
            '--gerrit-patchset=${patch_set}',
            '--buildbucket-id=${buildbucket_build_id}',
            # This normally evaluates to "0", but will evaluate to "1" if
            # "Use-Permissive-Angle-Pixel-Comparison: True" is present as a
            # CL footer.
            '--use-permissive-pixel-comparison=${use_permissive_angle_pixel_comparison}',
        ],
    },
    'timeout_120m': {
        'swarming': {
            'hard_timeout': 7200,
            'io_timeout': 300
        }
    },
}

MIXIN_FILE_NAME = os.path.join(THIS_DIR, 'mixins.pyl')
MIXINS_PYL_TEMPLATE = """\
# GENERATED FILE - DO NOT EDIT.
# Generated by {script_name} using data from {data_source}
#
# Copyright 2021 The ANGLE Project Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
#
# This is a .pyl, or "Python Literal", file. You can treat it just like a
# .json file, with the following exceptions:
# * all keys must be quoted (use single quotes, please);
# * comments are allowed, using '#' syntax; and
# * trailing commas are allowed.
#
# For more info see Chromium's mixins.pyl in testing/buildbot.

{mixin_data}
"""


def main():
    if len(sys.argv) > 1:
        gen_bb_json = os.path.join(TESTING_BBOT_DIR, 'generate_buildbot_json.py')
        mixins_pyl = os.path.join(TESTING_BBOT_DIR, 'mixins.pyl')
        inputs = [
            'test_suite_exceptions.pyl', 'test_suites.pyl', 'variants.pyl', 'waterfalls.pyl',
            gen_bb_json, mixins_pyl
        ]
        outputs = ['angle.json', 'mixins.pyl']
        if sys.argv[1] == 'inputs':
            print(','.join(inputs))
            return 0
        if sys.argv[1] == 'outputs':
            print(','.join(outputs))
            return 0

    # --verify-only enables dirty checks without relying on checked in hashes.
    # Compares the content of the existing file with the generated content.
    verify_only = '--verify-only' in sys.argv

    if verify_only:
        with tempfile.TemporaryDirectory() as temp_dir:
            return run_generator(verify_only, temp_dir)
    else:
        return run_generator(verify_only, None)


def write_or_verify_file(filename, content, verify_only):
    if verify_only:
        try:
            with open(filename) as f:
                # Note: .gitattributes "* text=auto" handles LF <-> CRLF on Windows
                return f.read() == content
        except FileNotFoundError:
            return False
    else:
        with open(filename, 'w') as fout:
            fout.write(content)
            return True


def run_generator(verify_only, temp_dir):
    chromium_args = generate_buildbot_json.BBJSONGenerator.parse_args([])
    chromium_generator = generate_buildbot_json.BBJSONGenerator(chromium_args)
    chromium_generator.load_configuration_files()

    override_args = ['--pyl-files-dir', THIS_DIR]
    if verify_only:
        override_args += ['--output-dir', temp_dir]
    angle_args = generate_buildbot_json.BBJSONGenerator.parse_args(override_args)
    angle_generator = generate_buildbot_json.BBJSONGenerator(angle_args)
    angle_generator.load_configuration_files()
    angle_generator.resolve_configuration_files()

    seen_mixins = set()
    for waterfall in angle_generator.waterfalls:
        seen_mixins = seen_mixins.union(waterfall.get('mixins', set()))
        for bot_name, tester in waterfall['machines'].items():
            seen_mixins = seen_mixins.union(tester.get('mixins', set()))
    for suite in angle_generator.test_suites.values():
        if isinstance(suite, list):
            # Don't care about this, it's a composition, which shouldn't include a
            # swarming mixin.
            continue
        for test in suite.values():
            assert isinstance(test, dict)
            seen_mixins = seen_mixins.union(test.get('mixins', set()))

    found_mixins = ADDITIONAL_MIXINS.copy()
    for mixin in seen_mixins:
        if mixin in found_mixins:
            continue
        assert (mixin in chromium_generator.mixins), 'Error with %s mixin' % mixin
        found_mixins[mixin] = chromium_generator.mixins[mixin]

    pp = pprint.PrettyPrinter(indent=2)

    format_data = {
        'script_name': os.path.basename(__file__),
        'data_source': 'waterfall.pyl and Chromium\'s mixins.pyl',
        'mixin_data': pp.pformat(found_mixins),
    }
    generated_mixin_pyl = MIXINS_PYL_TEMPLATE.format(**format_data)

    if not write_or_verify_file(MIXIN_FILE_NAME, generated_mixin_pyl, verify_only):
        print('infra/specs/mixins.pyl dirty')
        return 1

    if angle_generator.main() != 0:
        print('buildbot (pyl to json) generation failed')
        return 1

    if verify_only:
        for waterfall in angle_generator.waterfalls:
            filename = waterfall['name'] + '.json'  # angle.json, might have more in future
            with open(os.path.join(temp_dir, filename)) as f:
                content = f.read()
            angle_filename = os.path.join(THIS_DIR, filename)
            if not write_or_verify_file(angle_filename, content, True):
                print('infra/specs/%s dirty' % filename)
                return 1

    return 0


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main())
