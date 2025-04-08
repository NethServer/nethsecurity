# Netifyd closed-sources plugin
if [ -z "$NETIFYD_ACCESS_TOKEN" ]; then
    echo "Netifyd closed-sources plugin not enabled: skipping ns-dpi package"
    echo CONFIG_PACKAGE_ns-dpi=n >> .config
else
    echo "Netifyd closed-sources plugin enabled: enabling ns-dpi package"
    git clone "https://oauth2:$NETIFYD_ACCESS_TOKEN@gitlab.com/netify.ai/private/nethesis/netify-flow-actions.git"
    git clone "https://oauth2:$NETIFYD_ACCESS_TOKEN@gitlab.com/netify.ai/private/nethesis/netify-agent-stats-plugin.git"
    cat <<EOF >>.config
CONFIG_PACKAGE_netify-flow-actions=y
CONFIG_NETIFY_FLOW_ACTIONS_TARGET_LOG=y
CONFIG_NETIFY_FLOW_ACTIONS_TARGET_CTLABEL=y
CONFIG_NETIFY_FLOW_ACTIONS_TARGET_NFTSET=y
CONFIG_PACKAGE_netify-plugin-stats=y
EOF
fi

# Define the configuration
echo "Generating configuration..."
make defconfig

# Generate local build key
if [ -n "$USIGN_PUB_KEY" ] && [ -n "$USIGN_PRIV_KEY" ]; then
    echo "Using environment keys"
    echo "$USIGN_PUB_KEY" > ./key-build.pub
    echo "$USIGN_PRIV_KEY" > ./key-build
elif [ -f key-build.pub ] && [ -f key-build ]; then
    echo "Using existing keys to sign the build"
else
    echo "Generating local build key"
    #./staging_dir/host/bin/usign -G -s ./key-build -p ./key-build.pub -c "Local build key"
fi
