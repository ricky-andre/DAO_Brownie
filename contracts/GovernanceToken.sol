// SPDX-License-Identifier: MIT
pragma solidity ^0.8.2;

import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";

contract GovernanceToken is ERC20Votes {
    uint256 public s_maxSupply = 1000_000_000_000_000_000_000_000;

    constructor()
        ERC20("GovernanceToken", "GT")
        ERC20Permit("GovernanceToken")
    {
        address temp;
        _mint(msg.sender, s_maxSupply);
        temp = address(0x94DF0324e5099410EeA66e1e0EA6C5a799D75275);
        _mint(temp, s_maxSupply);
        temp = address(0xFa4679DD96C885D5487363f1321420BE451c5299);
        _mint(temp, s_maxSupply);
        temp = address(0xDdB340364b1a012F972e59B54786858962801e88);
        _mint(temp, s_maxSupply);
    }

    // The functions below are overrides required by Solidity.

    function _afterTokenTransfer(
        address from,
        address to,
        uint256 amount
    ) internal override(ERC20Votes) {
        super._afterTokenTransfer(from, to, amount);
    }

    function _mint(address to, uint256 amount) internal override(ERC20Votes) {
        super._mint(to, amount);
    }

    function _burn(address account, uint256 amount)
        internal
        override(ERC20Votes)
    {
        super._burn(account, amount);
    }
}
