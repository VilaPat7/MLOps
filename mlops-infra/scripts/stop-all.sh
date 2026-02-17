#!/bin/bash

echo "=== Stopping MLOps Infrastructure ==="
echo ""

# 1. Stop all port-forward processes
echo "1. Stopping all port-forward processes..."
pkill -f "kubectl port-forward" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ All port-forward processes stopped"
else
    echo "   ℹ️  No running port-forward processes found"
fi
sleep 2

# 2. Stop Minikube
echo "2. Stopping Minikube..."
minikube stop 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✅ Minikube stopped"
else
    echo "   ℹ️  Minikube was already stopped or not running"
fi

# 3. Optional: Delete all temporary files
echo "3. Cleaning up..."
rm -f /tmp/kubectl-* 2>/dev/null
echo "   ✅ Cleanup completed"

echo ""
echo "=== Infrastructure completely stopped ==="
echo ""
echo "To start everything again:"
echo "1. ./scripts/check-and-start.sh   # Check and start all components"
echo "2. ./scripts/access-all.sh        # Open access to all UIs"
echo ""
echo "To completely delete Minikube and all data:"
echo "minikube delete"
echo ""
echo "Note: All your data in Persistent Volumes will be preserved"
echo "      when you start Minikube again."
