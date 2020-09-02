ldap-ad
==========
Dynamic Ansible inventory script for Active Directory.
Modified version of https://github.com/rcanderson23/ldap-ad/

Differences:
* OU grouping is removed since i didn't need it. I also had a lot of OUs with duplicate names in my env, so OU grouping was not working and was breaking the script for me.
* LDAP filter includes lastlogontimestamp which allows to return only active computer accounts. The script will return computers that were active during the last 14 days. Number of days can be modified by editing the value of "lastlogondays" variable. LDAP filter also includes OS filter (only Windows Server computer account will be returned by default)
* Variables and creds are hardcoded (was acceptable in my case)
* Resulting inventory includes Ansible variables for Windows (can be modified in add_vars method).

Dependencies
==========
* python3
* ldap3

Installation
==========
1. Run `pip3 install -r requirements.txt`
2. Copy `ldap-ad.py` into your `/etc/ansible/inventory` folder


Configuration
==========
Customize variables in "init" and "add_vars" methods
