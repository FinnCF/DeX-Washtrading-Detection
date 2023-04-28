from web3 import Web3
import pandas as pd
from web3.exceptions import ContractLogicError
from web3.exceptions import ABIFunctionNotFound

ERC721_ABI = [{'inputs': [{'internalType': "bytes4",'name': "interfaceId",'type': "bytes4",},],'name': "supportsInterface",'outputs': [ {'internalType': "bool",'name': "",'type': "bool", },],'stateMutability': "view",'type': "function", },]
PROXY_ABI = [{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"stateMutability":"payable","type":"fallback"},{"inputs":[],"name":"implementation","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"stateMutability":"payable","type":"receive"}]

def get_all_transfer_events(w3, from_block, to_block):
    """
    Gets all transfer events from the from_block to the to_block.
    Requires a full node and chunking (to be implemented) for large ranges.
    """
    transfer_signature = w3.keccak(text="Transfer(address,address,uint256)").hex()

    filter = w3.eth.filter({'fromBlock': from_block, 'toBlock': to_block, "topics": [transfer_signature]})
    logs = w3.eth.get_filter_logs(filter.filter_id)
    
    transfer_events = []
    for log in logs:
        try:
            transfer_obs = {'address': log['address'],
                            'blockHash': log['blockHash'].hex(),
                            'blockNumber': log['blockNumber'],
                            'from_address':  Web3.to_checksum_address(log['topics'][1][-20:]),
                            'to_address': Web3.to_checksum_address(log['topics'][2][-20:]),
                            'token_id': int(log['data'].lstrip(b'\x00').hex(), 16),
                            'logIndex': log['logIndex'],
                            'transactionHash': log['transactionHash'].hex(),
                            'transactionIndex': log['transactionIndex']}
            transfer_events.append(transfer_obs)
        except Exception as e:
            continue
    print(f"{len(transfer_events)} Transfer Events Between: {from_block} To {to_block}")
    return transfer_events

def filter_NFT_compliance(transfer_events):
    """
    Filters transfer events to include only those that are ERC721 compliant
    or are proxies implementing ERC721 contracts.
    """
    filtered_events = []
    for transfer_obs in transfer_events:
        contract = w3.eth.contract(address=transfer_obs['address'], abi=ERC721_ABI)
        if is_certainly_erc721(contract):
            filtered_events.append(transfer_obs)
            continue  # Skip checking for proxies if it's already an ERC721 contract
        try:
            # Check if the contract is a proxy
            proxy_contract = w3.eth.contract(address=transfer_obs['address'], abi=PROXY_ABI)
            implementation_address = proxy_contract.functions.implementation().call()
            implementation_contract = w3.eth.contract(address=implementation_address, abi=ERC721_ABI)
            if is_certainly_erc721(implementation_contract):
                filtered_events.append(transfer_obs)
        except ABIFunctionNotFound as e:
            print(f"Error decoding function call for contract at address {transfer_obs['address']}: {e}")
            pass  # Ignore errors and continue to next contract
        except Exception as e:
            print(f"Error occurred while interacting with contract at address {transfer_obs['address']}: {e}")
            pass  # Ignore errors and continue to next contract

    return filtered_events

def is_certainly_erc721(contract):
    """
    Checks if the given contract is ERC721 compliant using the supportsInterface function.
    """
    erc721_interface_id = bytes.fromhex("80ac58cd")
    try:
        supports_erc721 = contract.functions.supportsInterface(erc721_interface_id).call()
        print(supports_erc721)
        return supports_erc721
    except Exception as e:
        #print(f"Exception occurred: {e}")
        return False

if __name__ == "__main__":
    w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/bd65e1b7072a41afa017a3f519f94e70'))
    current_block_number = w3.eth.block_number

    # Scan all 'Transfer' events that occured in the from - to period of blocks
    transfer_events = get_all_transfer_events(w3, current_block_number-1, current_block_number)
    filtered_events = filter_NFT_compliance(transfer_events)




