#!/bin/bash
# Monitor W1 Service CloudWatch Logs
# ===================================

source "$(dirname "$0")/config.sh"

echo "========================================="
echo "   W1 Service Log Monitor"
echo "========================================="

# Function to show logs for a specific Lambda
show_logs() {
    local function_name=$1
    local since=${2:-5m}
    
    echo ""
    echo "📋 Logs for ${function_name} (last ${since}):"
    echo "-------------------------------------------"
    
    aws logs tail "/aws/lambda/${function_name}" \
        --region "${AWS_REGION}" \
        --since "${since}" \
        --format short 2>/dev/null || echo "No recent logs"
}

# Function to show errors only
show_errors() {
    local function_name=$1
    local since=${2:-30m}
    
    echo ""
    echo "❌ Errors for ${function_name} (last ${since}):"
    echo "-------------------------------------------"
    
    aws logs tail "/aws/lambda/${function_name}" \
        --region "${AWS_REGION}" \
        --since "${since}" \
        --filter-pattern "ERROR" \
        --format short 2>/dev/null || echo "No errors found"
}

# Main menu
main_menu() {
    PS3="Select an option: "
    options=(
        "View all w1 function logs (last 5 min)"
        "View specific function logs"
        "View all errors (last 30 min)"
        "View WebSocket message logs"
        "View API logs"
        "Live tail logs"
        "Exit"
    )
    
    select opt in "${options[@]}"; do
        case $REPLY in
            1)
                for function in "${LAMBDA_FUNCTIONS[@]}"; do
                    show_logs "$function" "5m"
                done
                ;;
            2)
                echo "Available functions:"
                for i in "${!LAMBDA_FUNCTIONS[@]}"; do
                    echo "  $((i+1)). ${LAMBDA_FUNCTIONS[$i]}"
                done
                read -p "Select function number: " func_num
                if [[ $func_num -ge 1 && $func_num -le ${#LAMBDA_FUNCTIONS[@]} ]]; then
                    show_logs "${LAMBDA_FUNCTIONS[$((func_num-1))]}" "10m"
                fi
                ;;
            3)
                for function in "${LAMBDA_FUNCTIONS[@]}"; do
                    show_errors "$function" "30m"
                done
                ;;
            4)
                show_logs "w1-websocket-message" "10m"
                ;;
            5)
                show_logs "w1-conversation-api" "10m"
                ;;
            6)
                echo "Starting live tail for w1-websocket-message..."
                echo "Press Ctrl+C to stop"
                aws logs tail "/aws/lambda/w1-websocket-message" \
                    --region "${AWS_REGION}" \
                    --follow
                ;;
            7)
                echo "Exiting..."
                exit 0
                ;;
            *)
                echo "Invalid option"
                ;;
        esac
        echo ""
        echo "Press Enter to continue..."
        read
    done
}

# Quick mode for command line arguments
if [ "$1" == "errors" ]; then
    for function in "${LAMBDA_FUNCTIONS[@]}"; do
        show_errors "$function" "${2:-30m}"
    done
elif [ "$1" == "websocket" ]; then
    show_logs "w1-websocket-message" "${2:-10m}"
elif [ "$1" == "live" ]; then
    aws logs tail "/aws/lambda/w1-websocket-message" \
        --region "${AWS_REGION}" \
        --follow
elif [ -n "$1" ]; then
    show_logs "$1" "${2:-10m}"
else
    main_menu
fi