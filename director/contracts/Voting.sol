// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/**
 * Pametni ugovor za odobravanje zahteva vecinskim glasanjem.
 *
 * Ugovor se kreira po jednom zahtevu (kupovina ili prodaja imovine).
 * Samo unapred odabrani Ethereum racuni mogu da glasaju i to najvise
 * jednom po ugovoru. Zahtev se smatra prihvacenim / odbijenim kada
 * odgovarajuci broj glasova dostigne vecinu, odnosno n / 2 + 1, gde je
 * n ukupan broj dozvoljenih glasaca. Broj glasaca mora biti neparan.
 */
contract Voting {
    // jedinstveni identifikator zahteva iz Redis servisa
    string public orderUuid;

    address[] private voterList;
    mapping(address => bool) private allowedVoter;
    mapping(address => bool) private alreadyVoted;

    uint256 public approveVotes;
    uint256 public rejectVotes;
    uint256 public majority;

    bool public finished;
    bool public approved;

    event VoteCast(address indexed voter, bool approve);
    event VotingFinished(string orderUuid, bool approved);

    constructor(string memory _orderUuid, address[] memory _voters) {
        require(_voters.length > 0, "Empty voter list.");
        require(_voters.length % 2 == 1, "Even number of voters.");

        orderUuid = _orderUuid;

        for (uint256 i = 0; i < _voters.length; i++) {
            require(_voters[i] != address(0), "Invalid address.");
            if (!allowedVoter[_voters[i]]) {
                allowedVoter[_voters[i]] = true;
                voterList.push(_voters[i]);
            }
        }

        majority = _voters.length / 2 + 1;
    }

    /**
     * Glasanje za potvrdu (true) ili odbijanje (false) zahteva.
     */
    function vote(bool _approve) public {
        require(!finished, "Voting ended.");
        require(allowedVoter[msg.sender], "Invalid address.");
        require(!alreadyVoted[msg.sender], "Already voted.");

        alreadyVoted[msg.sender] = true;

        if (_approve) {
            approveVotes += 1;
        } else {
            rejectVotes += 1;
        }

        emit VoteCast(msg.sender, _approve);

        if (approveVotes >= majority) {
            finished = true;
            approved = true;
            emit VotingFinished(orderUuid, true);
        } else if (rejectVotes >= majority) {
            finished = true;
            approved = false;
            emit VotingFinished(orderUuid, false);
        }
    }

    function voters() public view returns (address[] memory) {
        return voterList;
    }

    function voterCount() public view returns (uint256) {
        return voterList.length;
    }

    function hasVoted(address _voter) public view returns (bool) {
        return alreadyVoted[_voter];
    }

    function isAllowed(address _voter) public view returns (bool) {
        return allowedVoter[_voter];
    }

    /**
     * status() vraca (da li je glasanje zavrseno, ishod, broj glasova za,
     * broj glasova protiv, potrebnu vecinu).
     */
    function status()
        public
        view
        returns (bool, bool, uint256, uint256, uint256)
    {
        return (finished, approved, approveVotes, rejectVotes, majority);
    }
}
