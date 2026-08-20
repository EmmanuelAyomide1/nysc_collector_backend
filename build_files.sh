set -e
echo "BUILD START" 
python3.12 -m pip install --break-system-packages -r requirements.txt 
python3.12 manage.py collectstatic --noinput --clear 
echo "BUILD END"