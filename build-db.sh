echo "Remove old database"
rm wfw.db3

echo "Create schema"
sqlite3 wfw.db3 < wfw-schema.sql

echo "Fill data?"
select yn in "Yes" "No"; do
    case $yn in
        Yes ) tar xf wfw-data.sql.tar.xz ; sqlite3 wfw.db3 < wfw-data.sql ; break;;
        No ) exit;;
    esac
done
