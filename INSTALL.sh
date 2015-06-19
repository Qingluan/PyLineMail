#! /usr/bin/env sh

sudo cp -a ../PyLineMail /usr/local/lib/python2.7/site-packages/ && sleep 1;

echo "cp script ok ";

sudo cp bin/email_send.py /usr/local/bin/PyMail && sleep 1;
echo "install ok ";

sudo chmod  +x /usr/local/bin/PyMail ;

echo "grant permission ok ";
#you can test if insgtall ok by PyMail --test

test=$(ls /usr/local/lib/python2.7/site-packages/ | grep mongo | wc | awk '{print $1}');

if [ $test -eq "0" ];
then
	echo "start install mongohelper from github";
	sudo wget -c -t 10 "https://raw.githubusercontent.com/Qingluan/QmongoHelper/master/install" | sh ;
fi

