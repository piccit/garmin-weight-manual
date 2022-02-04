import argparse
from ast import Num
import time
import sys
import os
import logging

# from datetime import date, datetime
from datetime import datetime
from tokenize import Number

from withings_sync.garmin import GarminConnect
from withings_sync.fit import FitEncoder_Weight


def get_args():
    parser = argparse.ArgumentParser(
        description=('A tool for synchronisation of Withings '
                     '(ex. Nokia Health Body) to Garmin Connect'
                     ' and Trainer Road.')
    )

    # def date_parser(s):
    #     return datetime.strptime(s, '%Y-%m-%d')

    parser.add_argument('--garmin-username', '--gu',
                        default=os.environ.get('GARMIN_USERNAME'),
                        type=str,
                        metavar='GARMIN_USERNAME',
                        help='username to login Garmin Connect.')
    parser.add_argument('--garmin-password', '--gp',
                        default=os.environ.get('GARMIN_PASSWORD'),
                        type=str,
                        metavar='GARMIN_PASSWORD',
                        help='password to login Garmin Connect.')

    parser.add_argument('--no-upload',
                        action='store_true',
                        help=('Won\'t upload to Garmin Connect and '
                              'output binary-strings to stdout.'))

    parser.add_argument('--verbose', '-v',
                        action='store_true',
                        help='Run verbosely')

    parser.add_argument('--weight', type=float)
    parser.add_argument('--fat', type=float)
    parser.add_argument('--muscle', type=float)

    return parser.parse_args()


def lbsToKg(lbs):
    return lbs * 0.453592


def sync(garmin_username, garmin_password,
         no_upload, verbose, weight, fat, muscle):

    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        stream=sys.stdout)

    # Create FIT file
    logging.debug('Generating fit file...')
    fit = FitEncoder_Weight()
    fit.write_file_info()
    fit.write_file_creator()

    dt = datetime.now()
    weight_kg = lbsToKg(weight)
    # percent_fat = 17.1
    muscle_mass_kg = lbsToKg(muscle)

    fit.write_device_info(timestamp=dt)
    fit.write_weight_scale(timestamp=dt,
                           weight=weight_kg,
                           percent_fat=fat,
                           muscle_mass=muscle_mass_kg)

    logging.debug('Record: %s weight=%s kg, '
                  'Percent Body Fat=%s %%, '
                  'muscle_mass=%s kg',
                  dt, weight_kg, fat,
                  muscle_mass_kg)

    fit.finish()

    if no_upload:
        fitValue = fit.getvalue()
        file = open("test.fit", "wb+")
        file.write(fitValue)
        # sys.stdout.buffer.write(fit.getvalue())
        return 0

    # Upload to Garmin Connect
    if garmin_username:
        garmin = GarminConnect()
        session = garmin.login(garmin_username, garmin_password)
        logging.debug('attempting to upload fit file...')
        r = garmin.upload_file(fit.getvalue(), session)
        if r:
            logging.info('Fit file uploaded to Garmin Connect')
    else:
        logging.info('No Garmin username - skipping sync')


args = get_args()
sync(**vars(args))
