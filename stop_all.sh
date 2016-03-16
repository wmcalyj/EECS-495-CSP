#!/bin/bash

echo "Start killing all workers (this sounds really bad T_T)"
ps -fA | grep "phantom_worker.js" | grep -v "grep" | awk '{print $2}' | xargs kill -9
echo "Start killing manager"
ps aux | grep "python" | grep -v "grep"| awk '{print $2}'  | xargs kill -9
echo "I am done, now check if anything is still running"
echo "check worker"
ps -fA | grep "phantom_worker.js" | grep -v "grep" 
echo "check manager"
ps aux | grep "python"