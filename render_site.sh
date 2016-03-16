#!/bin/bash

USAGE="
-------------------------------------------------------------------------------------
Other usage: ./render_site.sh -f <source_file> [-m <max_records>] [-d <log_level>]  |
For more help, please use ./render_site.sh -h                                       |
-------------------------------------------------------------------------------------

"

DEFAULT="
========================
Using default settings |
========================

"

HELP="
-h, --help         help
-ll, --loglevel    set log level: critical|error|warning|info(default)|debug
-lf, --logfile     set log file (default is crawler.log)
-f, --file         file to read from, please using relative path to the file
-m, --maxurls      max urls that will be allowed for single query
"

if [ -z $1 ]; then
  printf "${USAGE}"
  printf "${DEFAULT}"
else
  if [ "$1" == "-h" ] || [ $1 == "--help" ]; then
    printf "${HELP}"
    exit
  fi
fi

# Each time when we this command is run, rename the old output


# Create arcived folder if not exist
mkdir -p archived
# Move old files to archived
mv urls archived/urls-`date +"%m-%d-%y-%H-%M"`

file="sources.txt"
max_urls=3
log_level="INFO"
log_file="crawler.log"

while [[ $# > 1 ]]
do
key="$1"

case $key in
    -ll|--loglevel)
    log_level=`echo ${2} | tr '[a-z]' '[A-Z]'`
    shift # past argument
    ;;
    -lf|--logfile)
    log_file="$2"
    shift # past argument
    ;;
    -f|--file)
    file="$2"
    shift # past argument
    ;;
    -m|--maxurls)
    max_urls="$2"
    ;;
    *)
            # unknown option
    ;;
esac
shift # past argument or value
done

printf "reading from file: ${file}\n"
printf "max urls: ${max_urls}\n"
printf "log level: ${log_level}\n"
printf "log file: ${log_file}\n\n\n"

# Read contents from given file

printf "**************************** Start Crawling *********************************"

# Reading from files line by line
while IFS='' read -r line || [[ -n "$line" ]]; do
    printf "\n\nText read from file: $line\n"
    # For each line, separate by ";"
    IFS=";" read -a each_line <<< "$line"
    printf "domains: ${each_line[0]}\n"
    echo "urls: ${each_line[1]}"
    echo "cookies: ${each_line[2]}"
    # I don't include userAgent here becaue I want to leave it to 
    # phantom_manager to decide which userAgent to use.
    # printf "userAgent: ${each_line[3]}\n"


#--logfile=FILE          log file. if omitted stderr will be used
#--loglevel=LEVEL, -L LEVEL

    command="scrapy runspider --logfile=${log_file} -L ${log_level} python_crawler/python_crawler/spiders/my_spider.py -a domains=${each_line[0]} -a urls=${each_line[1]} -a maxurls=${max_urls} -a cookies=${each_line[2]} -a userAgent=${each_line[3]}"
    echo "running command: $command now!"
    scrapy runspider --logfile=${log_file} -L ${log_level} python_crawler/python_crawler/spiders/my_spider.py -a domains=${each_line[0]} -a urls=${each_line[1]} -a maxurls=${max_urls} -a cookies="${each_line[2]}" -a userAgent=${each_line[3]}

done < "$file"

outputDir="log_dir"

# After crawling urls, start phantom js
# python phantom_manager.py log_dir phanton_worker.js_path
echo "Start phantom_manager now, the output dir is ${outputDir}"
python CSP-Applier/training/phantom_manager.py $outputDir CSP-Applier/training/phantom_worker.js

