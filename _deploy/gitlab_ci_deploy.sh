#!/usr/bin/env bash
CR_PATH=`pwd`
GIT_CI_PATH='/home/cr'

time=$(date "+%Y%m%d-%H%M%S")
TMP_PATH="/gitlab_ci/"${time}"/"
TMP_CI_MIGRATIONS_PATH=${TMP_PATH}"migrations"
TMP_CI_CONFIG_PATH=${TMP_PATH}"config"

# backup migrations
mkdir -p ${TMP_CI_MIGRATIONS_PATH}
migrations=`find ${GIT_CI_PATH} -name "migrations"`

for migration in ${migrations}
do
    app_migrations_name=`echo ${migration##*${GIT_CI_PATH}}`
    app_name=`echo ${app_migrations_name%"/migrations"}`

    new_migrations_path=${TMP_CI_MIGRATIONS_PATH}${app_name}
    mkdir -p ${new_migrations_path}
    cp -r ${migration}"/" ${new_migrations_path}
done

# backup configure
mkdir -p ${TMP_CI_CONFIG_PATH}
config_path=${GIT_CI_PATH}"/cr/config.py"
setting_path=${GIT_CI_PATH}"/cr/settings.py"
cp ${config_path} ${TMP_CI_CONFIG_PATH}
cp ${setting_path} ${TMP_CI_CONFIG_PATH}

# mv bak
CR_BACKUP_PATH=${GIT_CI_PATH}".bak"
rm -rf ${CR_BACKUP_PATH}
mv ${GIT_CI_PATH} ${CR_BACKUP_PATH}

# cp src
cp -r ${CR_PATH} ${GIT_CI_PATH}

# copy migrations file
cd ${GIT_CI_PATH}
rm -rf */migrations
apps=`ls ${TMP_CI_MIGRATIONS_PATH}`
for app in ${apps}
do
    cp -rf ${TMP_CI_MIGRATIONS_PATH}"/"${app}"/migrations" ${GIT_CI_PATH}"/"${app}"/"
done

# copy configure
cp -f ${TMP_CI_CONFIG_PATH}"/config.py" ${config_path}
cp -f ${TMP_CI_CONFIG_PATH}"/settings.py" ${setting_path}

# make migrate
cd ${GIT_CI_PATH}
source /usr/bin/virtualenvwrapper.sh
workon cr
python manage.py makemigrations
python manage.py migrate
python manage.py compilemessages

# media
rm -rf ${GIT_CI_PATH}"/media"
ln -s /home/cr_media ${GIT_CI_PATH}"/media"

supervisorctl restart all
