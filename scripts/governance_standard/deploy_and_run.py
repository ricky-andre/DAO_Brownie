from scripts.helpful_scripts import LOCAL_BLOCKCHAIN_ENVIRONMENTS, get_account
from brownie import (
    GovernorContract,
    GovernanceToken,
    GovernanceTimeLock,
    Box,
    Contract,
    config,
    network,
    accounts,
    chain,
)
from web3 import Web3, constants

# Governor Contract
QUORUM_PERCENTAGE = 4
# VOTING_PERIOD = 45818  # 1 week - more traditional.
# You might have different periods for different kinds of proposals
VOTING_PERIOD = 10  # 10 blocks
VOTING_DELAY = 1  # 1 block

# Timelock
# MIN_DELAY = 3600  # 1 hour - more traditional
MIN_DELAY = 1  # 1 seconds

# Proposal
PROPOSAL_DESCRIPTION = "Proposal #1: Store 1 in the Box!"
NEW_STORE_VALUE = 5


def deploy_governor():
    """
    create the governor token and delegate a few accounts to vote,
    the others do not have rights to vote so their weight will be zero
    """
    account = get_account()
    tx = governance_token = (
        GovernanceToken.deploy(
            {"from": account},
            publish_source=config["networks"][network.show_active()].get(
                "verify", False),
        )
        if len(GovernanceToken) <= 0
        else GovernanceToken[-1]
    )
    for ind in range(4):
        account = get_account(ind)
        print(account.balance())
    for ind in range(4):
        tx = governance_token.delegate(
            get_account(ind), {"from": get_account(ind)})
        print(tx.info())
        print(
            f"Checkpoints: {governance_token.numCheckpoints(get_account(ind))}")
    governance_time_lock = governance_time_lock = (
        GovernanceTimeLock.deploy(
            MIN_DELAY,
            [],
            [],
            {"from": account},
            publish_source=config["networks"][network.show_active()].get(
                "verify", False
            ),
        )
        if len(GovernanceTimeLock) <= 0
        else GovernanceTimeLock[-1]
    )
    governor = GovernorContract.deploy(
        governance_token.address,
        governance_time_lock.address,
        QUORUM_PERCENTAGE,
        VOTING_PERIOD,
        VOTING_DELAY,
        {"from": account},
        publish_source=config["networks"][network.show_active()].get(
            "verify", False),
    )
    # Now, we set the roles...
    # Multicall would be great here ;)
    proposer_role = governance_time_lock.PROPOSER_ROLE()
    executor_role = governance_time_lock.EXECUTOR_ROLE()
    timelock_admin_role = governance_time_lock.TIMELOCK_ADMIN_ROLE()
    governance_time_lock.grantRole(proposer_role, governor, {"from": account})
    governance_time_lock.grantRole(
        executor_role, constants.ADDRESS_ZERO, {"from": account})
    tx = governance_time_lock.revokeRole(
        timelock_admin_role, account, {"from": account})
    tx.wait(1)
    # Guess what? Now you can't do anything!
    # governance_time_lock.grantRole(timelock_admin_role, account, {"from": account})
    return governance_token


def deploy_box_to_be_governed():
    account = get_account()
    box = Box.deploy({"from": account})
    tx = box.transferOwnership(GovernanceTimeLock[-1], {"from": account})
    tx.wait(1)


def propose(store_value):
    account = get_account()
    # We are going to store the number 1
    # With more args, just add commas and the items
    # This is a tuple
    # If no arguments, use `eth_utils.to_bytes(hexstr="0x")`
    args = (store_value,)
    # We could do this next line with just the Box object
    # But this is to show it can be any function with any contract
    # With any arguments
    encoded_function = Contract.from_abi("Box", Box[-1], Box.abi).store.encode_input(
        *args
    )
    print(encoded_function)
    propose_tx = GovernorContract[-1].propose(
        [Box[-1].address],
        [0],
        [encoded_function],
        PROPOSAL_DESCRIPTION,
        {"from": account},
    )
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        tx = account.transfer(accounts[0], "0 ether")
        tx.wait(1)
    propose_tx.wait(2)  # We wait 2 blocks to include the voting delay
    # This will return the proposal ID
    print(
        f"Proposal state {GovernorContract[-1].state(propose_tx.return_value)}")
    print(
        f"Proposal snapshot {GovernorContract[-1].proposalSnapshot(propose_tx.return_value)}")
    print(
        f"Proposal deadline {GovernorContract[-1].proposalDeadline(propose_tx.return_value)}")
    return propose_tx.return_value

# Can be done through a U


def vote(proposal_id: int, vote: int, account_ind: int):
    # 0 = Against, 1 = For, 2 = Abstain for this example
    # you can all the #COUNTING_MODE() function to see how to vote otherwise
    print(f"voting on {proposal_id} from account {account_ind}")
    account = get_account(index=account_ind)
    tx = GovernorContract[-1].castVoteWithReason(
        proposal_id, vote, "Cuz I lika do da cha cha", {"from": account})
    tx.wait(1)
    print(tx.info())
    print(tx.events["VoteCast"])


def queue_and_execute(store_value):
    account = get_account()
    # time.sleep(VOTING_PERIOD + 1)
    # we need to explicity give it everything, including the description hash
    # it gets the proposal id like so:
    # uint256 proposalId = hashProposal(targets, values, calldatas, descriptionHash);
    # It's nearlly exactly the same as the `propose` function, but we hash the description
    args = (store_value,)
    encoded_function = Contract.from_abi("Box", Box[-1], Box.abi).store.encode_input(
        *args
    )
    # this is the same as ethers.utils.id(description)
    description_hash = Web3.keccak(text=PROPOSAL_DESCRIPTION).hex()
    # if the proposal doesn't pass, everything is rejected and a
    # try/catch should be used to manage it.
    tx = GovernorContract[-1].queue(
        [Box[-1].address],
        [0],
        [encoded_function],
        description_hash,
        {"from": account},
    )
    tx.wait(1)
    print(f"Box before execution {Box[-1].retrieve()}")
    tx = GovernorContract[-1].execute(
        [Box[-1].address], [0], [encoded_function],
        description_hash, {"from": account},)
    tx.wait(1)
    print(f"Box after execution {Box[-1].retrieve()}")


def move_blocks(amount):
    for block in range(amount):
        get_account().transfer(get_account(), "0 ether")
    print(chain.height)


def main():
    """
    contains the deployment informations
    """
    deploy_governor()
    deploy_box_to_be_governed()
    proposal_id = propose(NEW_STORE_VALUE)
    print(f"Proposal ID {proposal_id}")
    # We do this just to move the blocks along
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        move_blocks(1)
    # we introduced here the possibility to vote for more accounts
    # 1 = for, 0=against, 2=don't care
    # below there are 2 votes for, 3 against, 2 don't care
    print("Starting to send votes")
    vote(proposal_id, 0, 0)
    vote(proposal_id, 1, 1)
    vote(proposal_id, 1, 2)
    vote(proposal_id, 2, 3)

    # Once the voting period is over,
    # if quorum was reached (enough voting power participated)
    # and the majority voted in favor, the proposal is
    # considered successful and can proceed to be executed.
    # To execute we must first `queue` it to pass the timelock
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        move_blocks(VOTING_PERIOD)
    # States: {Pending, Active, Canceled, Defeated, Succeeded, Queued, Expired, Executed }
    print(
        f" This proposal is currently {GovernorContract[-1].state(proposal_id)}")
    queue_and_execute(NEW_STORE_VALUE)
