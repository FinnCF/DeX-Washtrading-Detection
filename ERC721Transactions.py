from web3 import Web3
import pandas as pd

ERC721_ABI = [{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"owner","type":"address"},{"indexed":True,"internalType":"address","name":"approved","type":"address"},{"indexed":True,"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"Approval","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"owner","type":"address"},{"indexed":True,"internalType":"address","name":"operator","type":"address"},{"indexed":False,"internalType":"bool","name":"approved","type":"bool"}],"name":"ApprovalForAll","type":"event"},{"anonymous":False,"inputs":[{"indexed":True,"internalType":"address","name":"from","type":"address"},{"indexed":True,"internalType":"address","name":"to","type":"address"},{"indexed":True,"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"Transfer","type":"event"},{"inputs":[{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"approve","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"}],"name":"balanceOf","outputs":[{"internalType":"uint256","name":"balance","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"getApproved","outputs":[{"internalType":"address","name":"operator","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"owner","type":"address"},{"internalType":"address","name":"operator","type":"address"}],"name":"isApprovedForAll","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"name","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"ownerOf","outputs":[{"internalType":"address","name":"owner","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"safeTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"},{"internalType":"bytes","name":"data","type":"bytes"}],"name":"safeTransferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"operator","type":"address"},{"internalType":"bool","name":"_approved","type":"bool"}],"name":"setApprovalForAll","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"bytes4","name":"interfaceId","type":"bytes4"}],"name":"supportsInterface","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"symbol","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"tokenURI","outputs":[{"internalType":"string","name":"","type":"string"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"from","type":"address"},{"internalType":"address","name":"to","type":"address"},{"internalType":"uint256","name":"tokenId","type":"uint256"}],"name":"transferFrom","outputs":[],"stateMutability":"nonpayable","type":"function"}]

def get_erc721_transfer_events(w3, from_block, to_block):

    #Signature of transaction
    erc721_transfer_signature = w3.keccak(text="Transfer(address,address,uint256)").hex()
    erc721_interface_id = "0x80ac58cd"

    # Get logs for from block to the to block  
    filter = w3.eth.filter({'fromBlock': from_block, 'toBlock': to_block, "topics": [erc721_transfer_signature]})
    logs = w3.eth.get_filter_logs(filter.filter_id)
    
    erc721_contract = w3.eth.contract( abi=ERC721_ABI)

    transfer_data_list = []
    for log in logs:
        contract_address = log['address']
        erc721_contract = w3.eth.contract(address=contract_address, abi=ERC721_ABI)

        # Check if the contract supports ERC-721 interface by making a call. 
        try:
            erc721_contract.functions.supportsInterface(erc721_interface_id).call()
            from_address = Web3.to_checksum_address(log['topics'][1][-20:])
            to_address = Web3.to_checksum_address(log['topics'][2][-20:])
            token_id = int.from_bytes(log['data'], byteorder='big')
            transfer_data = {'address': contract_address,
                            'blockHash': log['blockHash'].hex(),
                            'blockNumber': log['blockNumber'],
                            'from_address': from_address,
                            'to_address': to_address,
                            'token_id': token_id,
                            'logIndex': log['logIndex'],
                            'transactionHash': log['transactionHash'].hex(),
                            'transactionIndex': log['transactionIndex']}
            transfer_data_list.append(transfer_data)
        except:  # Make an exception - if it doesnt ignore and continue looking over different logs. 
            continue
    
    transfers_pd = pd.DataFrame(columns=['address', 'blockHash', 'blockNumber', 'from_address', 'to_address', 'token_id', 'logIndex', 'transactionHash', 'transactionIndex'])    
    transfers_pd = pd.concat([pd.DataFrame(data=transfer_data_list)])
    transfers_pd.to_csv('New.csv')
    return transfers_pd

if __name__ == "__main__":
    w3 = Web3(Web3.HTTPProvider('https://mainnet.infura.io/v3/bd65e1b7072a41afa017a3f519f94e70'))
    current_block_number = w3.eth.block_number

    # Scan the last 2 blocks for ERC-721 transfer events
    erc721_transfer_events = get_erc721_transfer_events(w3, current_block_number - 1, current_block_number)
    print("ERC-721 Transfer Events: ", erc721_transfer_events)