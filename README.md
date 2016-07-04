# README

Simple Micro service for inbound and outbound sms.

Currently full code is written in single file.

It should be seperated as per the layer


####  To Run Local

1) Dump the postgresql data from testdatadump.txt

       psql -U <username> plivo <  testdatadump.txt
2) create virtual enviroment

       virtualvenv venvsms
       source venvsms/bin/activate
3) checkout the source code from
4) Install requirement files

        pip install -r requirements.txt

5) set enviorment variable

        export DATABASE_URL="postgresql://localhost/plivo"
        export APP_SETTINGS="config.StagingConfig"

6) Run the app, Default port http://127.0.0.1:5000/

        python src/sms_api.py

7) Curl request for Inbound

        curl -X POST -H "Authorization: Basic cGxpdm8xOjIwUzBLUE5PSU0=" \
             -H "Content-Type: application/json" \
             -d '{ "from" : "4924195509198",
                   "to" : "4924195509198",
                   "text" : "STOP, Hello World"
                }' "http://127.0.0.1:5000/inbound/sms/"

8) Curl request for Inbound

        curl -X POST -H "Authorization: Basic cGxpdm8xOjIwUzBLUE5PSU0=" \
             -H "Content-Type: application/json" \
             -d '{ "from" : "4924195509198",
                   "to" : "4924195509198",
                   "text" : "STOP, Hello World"
                }' "http://127.0.0.1:5000/outbound/sms/"
#### To test on local

1) set enviorment variable

        export DATABASE_URL="postgresql://localhost/plivo_testing"
        export APP_SETTINGS="config.TestingConfig"
2) Dump the postgresql data from testdatadump.txt

       psql -U <username> plivo_testing <  testdatadump.txt
3) create virtual enviroment

       virtualvenv venvsms
       source venvsms/bin/activate
4) Install requirement files

        pip install -r requirements.txt
5) Run the Testcase

        python src/test_sms_api.py

6) Total 16 testcase to cover the given scenario. Currently same db is used for testing .

   Enhancement : Test data can be generated automatically.


