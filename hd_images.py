import ftplib
import sqlite3
import os


def lowerCaseFiles():
    directory = 'images/inventory/'
    localFileList = os.listdir(directory)

    for fName in localFileList:
        path = directory + fName
        os.rename(path, path.replace(fName, fName.lower()))

    print(os.listdir(directory))


def autoUplinkFTP():

    # Login with credentials
    ftp = ftplib.FTP('ftp.autouplinktech.com')
    ftp.login('d-rmf7069', '9ziro9r')

    # Get list of files in ftp folder
    ftp_file_list = ftp.nlst()
    print('ftp.nlst():', ftp_file_list)

    if not ftp_file_list:
        print('No files found on AutoUplink FTP server.')
        return

    # Get list of files in local folder
    local_dir = 'images/inventory/'
    local_file_list = os.listdir(local_dir)

    # Download images from AutoUplink server
    for ftp_file_name in ftp_file_list:
        local_file_name = ftp_file_name.lower()
        if '.JPG' in ftp_file_name or '.jpg' in ftp_file_name:
            if local_file_name not in local_file_list:
                local_file_path = 'images/inventory/' + local_file_name
                local_file = open(local_file_path, 'wb')
                ftp.retrbinary('RETR ' + ftp_file_name, local_file.write, 1024)
                print('Saved ' + local_file_path + ' to local hard drive.')
                ftp.delete(ftp_file_name)
                print('Deleted ' + ftp_file_name + ' from AutoUplink FTP server.')
                local_file.close()
    ftp.quit()


def uploadImages():
    print('\nUploading HD images of inventory to FTP server at spencertichenor.com...')

    ftp = ftplib.FTP('spencertichenor.com')
    ftp.login('inventory_images@spencertichenor.com', 'M4lonePovolny')
    files = ftp.retrlines('LIST')
    print('files:', files)
    print('type', type(files))

    folder = 'images/inventory/'

    fileList = os.listdir(folder)
    for fileName in fileList:
        print('Uploading ' + fileName + ' to FTP server...\n')

        filePath = folder + fileName
        file = open(filePath, 'rb')
        fileName = fileName.replace('JPG', 'jpg')  # make jpg lowercase cuz outherwise it has to be uppercase for it to work as link
        ftp.storbinary('STOR ' + fileName, file, 1024)
        file.close()
        print('Successfully uploaded ' + fileName + '\n')

    ftp.quit()


def syncLocalWithFtp():
    print('\nUpdating image folder on FTP server at spencertichenor.com...')

    ftp = ftplib.FTP('spencertichenor.com')
    ftp.login('inventory-images@spencertichenor.com', 'M4lonePovolny')
    ftpFileList = ftp.nlst()

    localDir = 'images/inventory/'
    localFileList = os.listdir(localDir)

    # Upload inventory images from computer to spencertichenor.com
    upload_count = 0
    for i, localFileName in enumerate(localFileList):
        print('Image #{}/{}'.format(i + 1, len(localFileList)))
        if localFileName not in ftpFileList:
            localFilePath = localDir + localFileName
            file = open(localFilePath, 'rb')
            ftp.storbinary('STOR ' + localFileName, file, 1024)
            file.close()
            upload_count += 1
            print('Uploaded ' + localFileName + ' to spencertichenor.com')
        else:
            print(localFileName + ' already uploaded to spencertichenor.com')
            continue
    print('Uploaded {} images to spencertichenor.com.'.format(upload_count))

    # # Delete old pics from spencertichenor.com
    # delete_count = 0
    # ftpFileList = ftp.nlst()
    # for ftpFileName in ftpFileList:
    #     if ftpFileName not in localFileList and '.jpg' in ftpFileName:
    #         ftp.delete(ftpFileName)
    #         delete_count += 1
    #         print('Deleted ' + ftpFileName)
    #     else:
    #         print('No need to delete ' + ftpFileName)
    # print('Deleted {} images from spencertichenor.com.'.format(delete_count))

    # Update database with link to image
    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    c.execute('SELECT vin, imageUrlsHD FROM masterInventory')
    results = c.fetchall()
    ftpFileList = ftp.nlst()
    for fileName in ftpFileList:
        if '01.jpg' in fileName:  # Only if file is jpg and 01 so that we only get the first image
            print(fileName)
            vin = fileName[:-6].upper()
            url = 'http://spencertichenor.com/inventory-images/' + fileName
            print((vin, url))
            if (vin, url) not in results:
                c.execute('UPDATE masterInventory SET imageUrlsHD = ? WHERE vin = ?', (url, vin))
    conn.commit()
    conn.close()
    ftp.quit()


def delBusted():
    ftp = ftplib.FTP('spencertichenor.com')
    ftp.login('inventory-images@spencertichenor.com', 'M4lonePovolny')

    ftpFileList = ftp.nlst()
    for ftpFileName in ftpFileList:
        if '.JPG' in ftpFileName or '(1)' in ftpFileName:
            #ftp.delete(ftpFileName)
            print('Deleted ' + ftpFileName)
        else:
            print('No need to delete ', ftpFileName)

    localDir = 'images/inventory/'
    localFileList = os.listdir(localDir)
    print('local file list:', localFileList)
    for localFileName in localFileList:
        if '.JPG' in localFileName or '(1)' in localFileName:
            filePath = localDir + localFileName
            #os.remove(filePath)
            print('Deleted ' + localFileName)
        else:
            print('No need to delete ' + localFileName)





def deleteOldImages():  # Get's VINs for current inventory and pics saved to local hd, if pic is no longer in inventory, delete

    conn = sqlite3.connect('data/inventory.db')
    c = conn.cursor()
    c.execute('SELECT vin FROM masterInventory')
    results = c.fetchall()
    conn.close()

    vin_list = []
    for r in results:
        vin = r[0]
        vin_list.append(vin)

    # Delete old images from local hd
    file_list = os.listdir('images/inventory/')
    print(str(len(file_list)) + ' files found in Inventory directory.')
    local_file_count = len(file_list)
    local_delete_count = 0
    for file_name in file_list:
        path = 'images/inventory/' + file_name
        ext = os.path.splitext(path)[1]
        # print(ext)
        if ext == '.JPG' or ext == '.jpg':
            vin = file_name[:-6].upper()  # this could be done better
            print('vin', vin)
            if vin not in vin_list:
                os.remove('images/inventory/' + file_name)
                print('Deleted image ' + file_name)
                local_delete_count += 1
        else:
            print('File not of type .JPG')
            print(path, ext)



    # Delete old images from spencertichener.com
    ftp = ftplib.FTP('spencertichenor.com')
    ftp.login('inventory-images@spencertichenor.com', 'M4lonePovolny')

    ftp_file_list = ftp.nlst()
    ftp_file_count = len(ftp_file_list)
    ftp_delete_count = 0
    for ftp_file_name in ftp_file_list:
        if '.jpg' in ftp_file_name:
            vin = ftp_file_name[:-6].upper()
            print('VIN:', vin)
            if vin not in vin_list:
                ftp.delete(ftp_file_name)
                ftp_delete_count += 1
                print('Deleted ' + ftp_file_name)
            else:
                print('No need to delete ' + ftp_file_name)

    print('Deleted {}/{} images from local hd.'.format(local_delete_count, local_file_count))
    print('Deleted {}/{} images from spencertichenor.com.'.format(ftp_delete_count, ftp_file_count))


def main():
    autoUplinkFTP()
    syncLocalWithFtp()
    deleteOldImages()
    delBusted()


if __name__ == '__main__':
    main()
