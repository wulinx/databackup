#!usr/bin/env python
# -*- coding:utf-8 -*-
"""
 This script is used to backup files on ubuntu servers to 10.10.20.218 data server,
 which includes incremental backup method and an email function to notice the net-manager
 wether the backup work is done
"""
import os
from fabric.api import * #run, env,hosts
from datetime import date,timedelta  # for data caculation
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email.Utils import formatdate
from email import Encoders
import time


env.hosts = ['spig@10.10.20.218','spig@10.10.20.218','spig@10.10.20.220','user@10.10.20.221','spig@10.10.20.224']
env.user='spig'
env.password='spig'
env.passwords={'wulin@10.10.20.174':'spig','spig@10.10.20.218':'spig','spig@10.10.20.220':'ab12cd',\
               'user@10.10.20.221':'user','spig@10.10.20.224':'ab12cd'}
env.timeout=60

def Test():
    run('pwd')
    print 'Test is OK'

@hosts('spig@10.10.20.220')
def Backup220():
    """FOR 10.10.20.220 mysql iot-erp jira kb opendj"""
    weekday={1:'Monday',2:'Tuesday',3:'Wensday',4:'Thusday',5:'Friday',6:'Saturday',7:'Sunday'}
    Day=date.today()
    Day=date(2012,5,6)
 #   Day=date(2012,4,22)
    print 'Backup time......'
    print 'Today is',Day,weekday[Day.isoweekday()]

    env.localDirOpenDJ='/home/spig/OpenDJ/bak/'

#  DO Incremental backup for opendj everyday and don't change the objective dir
    run('/home/spig/OpenDJ/bin/backup --port 4444 --bindDN "cn=Directory Manager" --bindPassword "ab12cd" \
        --backUpAll --backupDirectory /home/spig/OpenDJ/bak --start 0 --trustAll')

    env.cmdOption='-va --partial --progress --delete --password-file=/etc/rsync_client.pass'
    env.remoteDir='spig@10.10.20.218::backup220/OpenDJ/'
 #   if not os.path.exists(env.remoteDir):
 #          local('mkdir -p %s'% env.remoteDir)
    print 10*'-','Now start  backup for opendj!',10*'-'
    run('rsync %s %s %s ' % (env.cmdOption,env.localDirOpenDJ,env.remoteDir))
    print 10*'-',' backup of opendj on 10.10.20.220  is finished!',10*'-'        
  # OpenDj is OK!
    print ("~"+os.linesep)*6
# Do full backup for mysql

    env.local='/home/spig/temp/backformysql/'
    if not os.path.exists(env.local):
       run('mkdir -p %s'% env.local)
    run('mysqldump -uroot -pab12cd -A >%smysql%s.bak'%(env.local,Day))
    env.cmdOption='-va --partial --progress --delete --password-file=/etc/rsync_client.pass'
    env.remoteDir='spig@10.10.20.218::backup220/Mysql/%s/%s/%s/'%(Day.year,Day.month,Day)
    env.temp='/home/spig/databackup/backup220/Mysql/%s/%s/%s/'%(Day.year,Day.month,Day)
    if not os.path.exists(env.temp):
           local('mkdir -p %s'% env.temp)
    print 10*'-',"Now start Full backup for mysql !",10*'-'
    run('rsync %s %s %s ' % (env.cmdOption,env.local,env.remoteDir))
    run('rm -rf /home/spig/temp/backformysql/*')            #remove the dumped data on 220
    print 10*'-',"backup of mysql is finished",10*'-'
# mysql is ok 
    print ("~"+os.linesep)*6

#do backup for erp
    if 7==Day.isoweekday():
        print 15*'*','And today is a Full Backup day for erp ',15*'*'
        env.localDirErp='/var/www/media/erp/'   #dir needed to be backuped
        env.cmdOption='-va --partial --progress --delete --password-file=/etc/rsync_client.pass'
        env.temp='/home/spig/databackup/backup220/Erp/%s/%s/Full/'%(Day.year,Day)
        env.remoteDir='spig@10.10.20.218::backup220/Erp/%s/%s/Full/'% (Day.year,Day)# 10.10.20.218 machine
        if not os.path.exists(env.temp):
            local('mkdir -p %s'% env.temp)

        print 10*'-',"Now start Full backup!",10*'-'
        run('rsync %s %s %s' % (env.cmdOption,env.localDirErp,env.remoteDir))
        print 10*'-',"Full backup is finished!",10*'-'

        if Day.day<=7:
            print 15*"*","Today is the first Sunday of a month, we will remove some of the backuped data of previous month",15*'*'
            env.rem='/home/spig/databackup/backup220/Erp/%s/%s/'%(Day.year,Day-timedelta(days=14))
            if os.path.exists(env.rem):
                local('rm -r %s'%(env.rem))
            env.rem='/home/spig/databackup/backup220/Erp/%s/%s/'%(Day.year,Day-timedelta(days=21))
            if os.path.exists(env.rem):
                local('rm -r %s'%(env.rem))
            env.rem='/home/spig/databackup/backup220/Erp/%s/%s/'%(Day.year,Day-timedelta(days=28))
            if os.path.exists(env.rem):
                local('rm -r %s'%(env.rem))
            print 15*'*',"remove work is done , and only data of  last week of previos month is reserved ",15*'*'

    else:
        print 15*'*','And today is an Incremental Backup day for erp',15*'*'
        env.localDirErp='/var/www/media/erp/'   #dir needed to be backuped
        env.remoteDir='spig@10.10.20.218::backup220/Erp/%s/%s/Full/'%\
            (Day.year,Day-timedelta(days=Day.isoweekday()))# 10.10.20.218 machine

        env.temp='/home/spig/databackup/backup220/Erp/%s/%s/Incremental/%s%s' \
                %(Day.year,Day-timedelta(days=Day.isoweekday()),Day,weekday[Day.isoweekday()])
        env.cmdOption='-va --partial --progress --delete --password-file=/etc/rsync_client.pass\
            --backup --backup-dir=/Erp/%s/%s/Incremental/%s%s'%(Day.year,Day-timedelta(days=Day.isoweekday())\
                ,Day,weekday[Day.isoweekday()])
        if not os.path.exists(env.temp):
             local('mkdir -p %s'% env.temp)
        # print env.cmdOption
        print 10*'-',"Now start Incremental backup!",10*'-'
        run('rsync %s %s %s ' % (env.cmdOption,env.localDirErp,env.remoteDir))
        print 10*'-',"Incremental backup is finished!",10*'-'
    print 15*'*','Today\'s work is for erp is done!',15*'*'

    print ("~"+os.linesep)*6
#do backup for jira on 220
    if 7==Day.isoweekday():
        print 15*'*','And today is a Full Backup day for jira ',15*'*'
        env.cmdOption='-va --partial --progress --delete --password-file=/etc/rsync_client.pass'
        env.localDirJIRA='/var/lib/jira-home-433/data/'
        env.temp='/home/spig/databackup/backup220/JIRA/%s/%s/Full/'%(Day.year,Day)
        env.remoteDir='spig@10.10.20.218::backup220/JIRA/%s/%s/Full/'% (Day.year,Day)# 10.10.20.218 machine
        if not os.path.exists(env.temp):
            local('mkdir -p %s'% env.temp)

        print 10*'-',"Now start Full backup!",10*'-'
        run('rsync %s %s %s' % (env.cmdOption,env.localDirJIRA,env.remoteDir))
        print 10*'-',"Full backup is finished!",10*'-'
        if Day.day<=7:
            print 15*"*","Today is the first Sunday of a month, we will remove some of the backuped data of previous month",15*'*'
            env.rem='/home/spig/databackup/backup220/JIRA/%s/%s/'%(Day.year,Day-timedelta(days=14))
            if os.path.exists(env.rem):
                local('rm -r %s'%(env.rem))
            env.rem='/home/spig/databackup/backup220/JIRA/%s/%s/'%(Day.year,Day-timedelta(days=21))
            if os.path.exists(env.rem):
                local('rm -r %s'%(env.rem))
            env.rem='/home/spig/databackup/backup220/JIRA/%s/%s/'%(Day.year,Day-timedelta(days=28))
            if os.path.exists(env.rem):
                local('rm -r %s'%(env.rem))
            print 15*'*',"remove work is done , and only data of  last week of previos month is reserved ",15*'*'

    else:
        print 15*'*','And today is an Incremental Backup day for jira',15*'*'
        env.localDirJIRA='/var/lib/jira-home-433/data/'
        env.remoteDir='spig@10.10.20.218::backup220/JIRA/%s/%s/Full/'%\
            (Day.year,Day-timedelta(days=Day.isoweekday()))# 10.10.20.218 machine

        env.temp='/home/spig/databackup/backup220/JIRA/%s/%s/Incremental/%s%s' \
                %(Day.year,Day-timedelta(days=Day.isoweekday()),Day,weekday[Day.isoweekday()])
        env.cmdOption='-va --partial --progress --delete --password-file=/etc/rsync_client.pass\
            --backup --backup-dir=/JIRA/%s/%s/Incremental/%s%s'%(Day.year,Day-timedelta(days=Day.isoweekday())\
                ,Day,weekday[Day.isoweekday()])
        if not os.path.exists(env.temp):
             local('mkdir -p %s'% env.temp)
        # print env.cmdOption
        print 10*'-',"Now start Incremental backup!",10*'-'
        run('rsync %s %s %s ' % (env.cmdOption,env.localDirJIRA,env.remoteDir))
        print 10*'-',"Incremental backup is finished!",10*'-'
    print 15*'*','Today\'s work is for jira  done!',15*'*'
    print ("~"+os.linesep)*6

#do backup for kb on 220
    if 7==Day.isoweekday():
        print 15*'*','And today is a Full Backup day for kb ',15*'*'
        env.cmdOption='-va --partial --progress --delete --password-file=/etc/rsync_client.pass'
        env.localDirKB='/var/lib/confluence-home/attachments/'
        env.temp='/home/spig/databackup/backup220/KB/%s/%s/Full/'%(Day.year,Day)
        env.remoteDir='spig@10.10.20.218::backup220/KB/%s/%s/Full/'% (Day.year,Day)# 10.10.20.218 machine
        if not os.path.exists(env.temp):
            local('mkdir -p %s'% env.temp)

        print 10*'-',"Now start Full backup!",10*'-'
        run('rsync %s %s %s' % (env.cmdOption,env.localDirKB,env.remoteDir))
        print 10*'-',"Full backup is finished!",10*'-'
        if Day.day<=7:
            print 15*"*","Today is the first Sunday of a month, we will remove some of the backuped data of previous month",15*'*'
            env.rem='/home/spig/databackup/backup220/KB/%s/%s/'%(Day.year,Day-timedelta(days=14))
            if os.path.exists(env.rem):
                local('rm -r %s'%(env.rem))
            env.rem='/home/spig/databackup/backup220/KB/%s/%s/'%(Day.year,Day-timedelta(days=21))
            if os.path.exists(env.rem):
                local('rm -r %s'%(env.rem))
            env.rem='/home/spig/databackup/backup220/KB/%s/%s/'%(Day.year,Day-timedelta(days=28))
            if os.path.exists(env.rem):
                local('rm -r %s'%(env.rem))
            print 15*'*',"remove work is done , and only data of  last week of previos month is reserved ",15*'*'

    else:
        print 15*'*','And today is an Incremental Backup day for KB',15*'*'
        env.localDirKB='/var/lib/confluence-home/attachments/'
        env.remoteDir='spig@10.10.20.218::backup220/KB/%s/%s/Full/'%\
            (Day.year,Day-timedelta(days=Day.isoweekday()))# 10.10.20.218 machine

        env.temp='/home/spig/databackup/backup220/KB/%s/%s/Incremental/%s%s' \
                %(Day.year,Day-timedelta(days=Day.isoweekday()),Day,weekday[Day.isoweekday()])
        env.cmdOption='-va --partial --progress --delete --password-file=/etc/rsync_client.pass\
            --backup --backup-dir=/KB/%s/%s/Incremental/%s%s'%(Day.year,Day-timedelta(days=Day.isoweekday())\
                ,Day,weekday[Day.isoweekday()])
        if not os.path.exists(env.temp):
             local('mkdir -p %s'% env.temp)
        # print env.cmdOption
        print 10*'-',"Now start Incremental backup!",10*'-'
        run('rsync %s %s %s ' % (env.cmdOption,env.localDirKB,env.remoteDir))
        print 10*'-',"Incremental backup is finished!",10*'-'
    print 15*'*','Today\'s work is for kb  done!',15*'*'
    print ("~"+os.linesep)*6


@hosts('user@10.10.20.221')
def Backup221():
    """FOR 10.10.20.221  mysql quickbuild"""
    weekday={1:'Monday',2:'Tuesday',3:'Wensday',4:'Thusday',5:'Friday',6:'Saturday',7:'Sunday'}
    Day=date.today()
    Day=date(2012,5,6)
 #   Day=date(2012,4,22)
    print 'Backup time......'
    print 'Today is',Day,weekday[Day.isoweekday()]

    env.cmdOption='-va --partial --progress --delete --password-file=/etc/rsync_client.pass'
    env.localDirQuick='/home/user/backup/'
    env.temp='/home/spig/databackup/backup221/QuickBuild/%s/'%(Day.year)
    env.remoteDir='spig@10.10.20.218::backup221/QuickBuild/%s/'% (Day.year)# 10.10.20.218 machine
    if not os.path.exists(env.temp):
        local('mkdir -p %s'% env.temp)
    print 10*'-',"Now start  backup!",10*'-'
    run('rsync %s %s %s' % (env.cmdOption,env.localDirQuick,env.remoteDir))
    print 10*'-'," backup is finished!",10*'-'
    print ("~"+os.linesep)*6

# Do full backup for mysql
    env.local='/home/user/temp/backformysql/'
    if not os.path.exists(env.local):
       run('mkdir -p %s'% env.local)
    run('mysqldump -uroot -proot -A >%smysql%s.bak'%(env.local,Day))
    env.cmdOption='-va --partial --progress --delete --password-file=/etc/rsync_client.pass'
    env.remoteDir='spig@10.10.20.218::backup221/Mysql/%s/%s/%s/'%(Day.year,Day.month,Day)
    env.temp='/home/spig/databackup/backup221/Mysql/%s/%s/%s/'%(Day.year,Day.month,Day)
    if not os.path.exists(env.temp):
           local('mkdir -p %s'% env.temp)
    print 10*'-',"Now start Full backup for mysql !",10*'-'
    run('rsync %s %s %s ' % (env.cmdOption,env.local,env.remoteDir))
    run('rm -rf /home/user/temp/backformysql/*')            #remove the dumped data on 221
    print 10*'-',"backup of mysql is finished",10*'-'
# mysql is ok 
    print ("~"+os.linesep)*6


@hosts('spig@10.10.20.224')
def Backup224():
    """FOR 10.10.20.224  mysql hg"""
    weekday={1:'Monday',2:'Tuesday',3:'Wensday',4:'Thusday',5:'Friday',6:'Saturday',7:'Sunday'}
    Day=date.today()
    Day=date(2012,5,6)
    print 'Backup time......'
    print 'Today is',Day,weekday[Day.isoweekday()]

# Do full backup for mysql
    env.local='/home/spig/temp/backformysql/'
    if not os.path.exists(env.local):
       run('mkdir -p %s'% env.local)
    run('mysqldump -uroot -pab12cd -A >%smysql%s.bak'%(env.local,Day))
    env.cmdOption='-va --partial --progress --delete --password-file=/etc/rsync_client.pass'
    env.remoteDir='spig@10.10.20.218::backup224/Mysql/%s/%s/%s/'%(Day.year,Day.month,Day)
    env.temp='/home/spig/databackup/backup224/Mysql/%s/%s/%s/'%(Day.year,Day.month,Day)
    if not os.path.exists(env.temp):
           local('mkdir -p %s'% env.temp)
    print 10*'-',"Now start Full backup for mysql !",10*'-'
    run('rsync %s %s %s ' % (env.cmdOption,env.local,env.remoteDir))
    run('rm -rf /home/user/temp/backformysql/*')            #remove the dumped data on 224
    print 10*'-',"backup of mysql is finished",10*'-'
# mysql is ok 
    print ("~"+os.linesep)*6


#Do backup for hg
    if 7==Day.isoweekday():
        print 15*'*','And today is a Full Backup day for hg ',15*'*'
        env.cmdOption='-va --partial --progress --delete --password-file=/etc/rsync_client.pass'
        env.localDirHG='/srv/hg/'
        env.temp='/home/spig/databackup/backup224/HG/%s/%s/Full/'%(Day.year,Day)
        env.remoteDir='spig@10.10.20.218::backup224/HG/%s/%s/Full/'% (Day.year,Day)# 10.10.20.218 machine
        if not os.path.exists(env.temp):
            local('mkdir -p %s'% env.temp)

        print 10*'-',"Now start Full backup!",10*'-'
        run('rsync %s %s %s' % (env.cmdOption,env.localDirHG,env.remoteDir))
        print 10*'-',"Full backup is finished!",10*'-'
        if Day.day<=7:
            print 15*"*","Today is the first Sunday of a month, we will remove some of the backuped data of previous month",15*'*'
            env.rem='/home/spig/databackup/backup224/HG/%s/%s/'%(Day.year,Day-timedelta(days=14))
            if os.path.exists(env.rem):
                local('rm -r %s'%(env.rem))
            env.rem='/home/spig/databackup/backup224/HG/%s/%s/'%(Day.year,Day-timedelta(days=21))
            if os.path.exists(env.rem):
                local('rm -r %s'%(env.rem))
            env.rem='/home/spig/databackup/backup224/HG/%s/%s/'%(Day.year,Day-timedelta(days=28))
            if os.path.exists(env.rem):
                local('rm -r %s'%(env.rem))
            print 15*'*',"remove work is done , and only data of  last week of previos month is reserved ",15*'*'
    else:
        print 15*'*','And today is an Incremental Backup day for HG',15*'*'
        env.localDirHG='/srv/hg/'
        env.remoteDir='spig@10.10.20.218::backup224/HG/%s/%s/Full/'%\
            (Day.year,Day-timedelta(days=Day.isoweekday()))# 10.10.20.218 machine

        env.temp='/home/spig/databackup/backup224/HG/%s/%s/Incremental/%s%s' \
                %(Day.year,Day-timedelta(days=Day.isoweekday()),Day,weekday[Day.isoweekday()])
        env.cmdOption='-va --partial --progress --delete --password-file=/etc/rsync_client.pass\
            --backup --backup-dir=/HG/%s/%s/Incremental/%s%s'%(Day.year,Day-timedelta(days=Day.isoweekday())\
                ,Day,weekday[Day.isoweekday()])
        if not os.path.exists(env.temp):
             local('mkdir -p %s'% env.temp)
        # print env.cmdOption
        print 10*'-',"Now start Incremental backup!",10*'-'
        run('rsync %s %s %s ' % (env.cmdOption,env.localDirHG,env.remoteDir))
        print 10*'-',"Incremental backup is finished!",10*'-'
    print 15*'*','Today\'s work is for HG  done!',15*'*'
    print ("~"+os.linesep)*6

@hosts('spig@10.10.20.218')
def DealWin219():
    """Deal with the backed file of 10.10.20.219"""
    weekday={1:'Monday',2:'Tuesday',3:'Wensday',4:'Thusday',5:'Friday',6:'Saturday',7:'Sunday'}
    Day=date.today()
    Day=date(2012,5,6)
    if 7==Day.isoweekday():
        print 'Today is',Day,weekday[Day.isoweekday()]
        print 10*'*', "Now let's deal with win 10.10.20.219 ",10*'*'
        if os.path.exists('/home/spig/databackup/backup219Win/win219.bkf'):
           print "move the win219 to dir %s"%(Day)
           NewDir='/home/spig/databackup/backup219Win/%s_%s'%(Day-timedelta(days=7),Day-timedelta(days=1))
           local('mkdir -p %s'%(NewDir) )
           local('mv /home/spig/databackup/backup219Win/win219.bkf %s/win219.bkf'%(NewDir))
           print "move work is done"

    print ("~"+os.linesep)*6
    print 'CHECK CHECK CHECK'

@hosts('spig@10.10.20.218')
def SendEmail():
    """Send mail to notify wether the backup work is done sucessfully"""

    print 5*os.linesep
    print "Today is %s"%(date.today())
    smtpserver = 'smtp.insigma.com.cn'
    smtpuser = 'spig@insigma.com.cn'
    smtppass = '123456'
    smtpport = 587

    MailTo=["wulin@insigma.com.cn","yangyubo@insigma.com.cn"]
    MailTo=["wulin@insigma.com.cn"]
    assert type(MailTo) == list
    msg = MIMEMultipart()   ## 创建MIME，并添加信息头
    msg['From'] = smtpuser
    msg['To'] = ','.join(MailTo)
    msg['Date'] = formatdate(localtime=True)   #获取当前时间
 
    filename='/home/spig/BackupLog.log'
    flag=False #标记是否找到
    if os.path.exists(filename):
        print "check whether the backup is ok?"
        f=open(filename,'rb')
        for eachline in f:
            if 'CHECK CHECK CHECK'==eachline.strip():
            	flag=True
        f.close()
        if True==flag:
            MailSubject="[IOT-BAK]对%s日的数据备份成功,具体情况请见附件"%(date.today()-timedelta(days=1))
            MailText="对%s日的数据备份成功,具体情况请见附件."%(date.today()-timedelta(days=1))+os.linesep+\
                            "10.10.20.220 : mysql IOT-ERP JIRA KB OpenDJ  备份OK"\
                             +os.linesep+"10.10.20.221: quickbuild mysql   备份OK" +os.linesep+"10.10.20.224 mysql IOT-HG  备份OK"+os.linesep\
                             +"10.10.20.219: 目录调整OK"+os.linesep+"相关日志在附件中,如有必要请查阅"
        else:
            MailSubject="[IOT-BAK]对%s日的数据备份失败,请检查10.10.20.218"%(date.today()-timedelta(days=1))
            MailText="对%s日的数据备份失败,请检查10.10.20.218"%(date.today()-timedelta(days=1))+os.linesep+\
                     "具体情况为:未能在最近的一次备份的日志文件中找到备份正确结束的标志行:'CHECK CHECK CHECK',应该是上一次备份在备份中途停止了"+\
                     os.linesep+"相关日志在附件中,请查阅附件"
        msg['Subject'] = MailSubject    #正文 字符串
        msg.attach(MIMEText(MailText, 'plain', 'utf-8'))   #邮件正文
        data = open(filename, 'rb')          ## 读入文件内容并格式化
        mimetype = "text/plain"
        maintype,subtype = mimetype.split("/")
        file_msg = MIMEBase(maintype, subtype)    # 构造MIMEBase对象
        file_msg.set_payload(data.read())   #读取数据
        data.close()
        Encoders.encode_base64(file_msg)
        ## 设置附件头
        file_msg.add_header('Content-Disposition', 'attachment; filename="%s"'% os.path.basename(filename))
        msg.attach(file_msg)     #附加到根容器
        print "附件构建OK "
    else:
        MailSubject="[IOT-KB]对%s日的数据备份失败,请检查10.10.20.218"%(date.today()-timedelta(days=1))
        MailText="对%s日的数据备份失败,请检查10.10.20.218"%(date.today()-timedelta(days=1))+os.linesep+\
                 "具体情况为: 在发送提示邮件的时候未能检查到最近一次备份的日志文件,应该是上一次备份没有运行,或者备份在中途停止了"
        msg['Subject'] = MailSubject    #正文 字符串
        msg.attach(MIMEText(MailText, 'plain', 'utf-8'))   #邮件正文
    print MailText
    try:
        smtp = smtplib.SMTP()
        smtp.connect(smtpserver,smtpport)
        smtp.login(smtpuser, smtppass)
        smtp.sendmail(smtpuser,MailTo , msg.as_string())
        smtp.quit()
    except Exception, e:
        print e, "the email send failure"

    print "Email is send"

if __name__ == '__main__':
    
    Test()

