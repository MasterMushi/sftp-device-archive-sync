import configparser
import logging
import os
import paramiko
import pysftp
import sys

from stat import S_ISDIR, S_ISREG


def get_r_portable(sftp, remotedir, localdir, preserve_mtime=False):
    for entry in sftp.listdir_attr(remotedir):
        remotepath = remotedir + "/" + entry.filename
        localpath = os.path.join(localdir, entry.filename)
        mode = entry.st_mode
        if S_ISDIR(mode):
            try:
                os.mkdir(localpath)
            except OSError:
                pass
            get_r_portable(sftp, remotepath, localpath, preserve_mtime)
        elif S_ISREG(mode):
            if (os.path.isfile(localpath)):
                if (os.path.getmtime(localpath) != entry.st_mtime):
                    os.remove(localpath)
                    sftp.get(remotepath, localpath,
                             preserve_mtime=preserve_mtime)
                    logger.info(f'File {localpath} replacemented')
            else:
                sftp.get(remotepath, localpath,
                         preserve_mtime=preserve_mtime)
                logger.info(f'File {localpath} received')


if __name__ == '__main__':
    logging.basicConfig(filename='sync.log', filemode='a',
                        format='%(asctime)s: %(levelname)s: %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        level=logging.CRITICAL)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    cwd = os.path.dirname(os.path.realpath(__file__))
    dev_ini_path = os.path.join(cwd, 'Device.ini')
    config = configparser.ConfigParser()
    config.read(dev_ini_path)

    dev_count = int(config['BASE']['Count'])

    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None

    for i in range(1, dev_count + 1):
        dev = config[f'DEVICE_{i}']
        moxa_ip = dev['MOXA']
        sftp_folder = dev['FTP_Folder']
        backup = dev['Backup']

        os.makedirs(backup, exist_ok=True)

        try:
            with pysftp.Connection(host=moxa_ip, username='moxa',
                                   password='moxa', cnopts=cnopts) as sftp:
                logger.info(f'Connection to {moxa_ip} succesfully established...')
                get_r_portable(sftp=sftp,
                               remotedir=sftp_folder,
                               localdir=backup,
                               preserve_mtime=True)
                logger.info(f'Get files from {sftp_folder} to {backup}')
                logger.info(f'Connection to {moxa_ip} is closing...')
        except paramiko.SSHException:
            logger.warning(f'Connection to {moxa_ip} not established!')

    logger.info('Application is closing...\n')
    sys.exit()
