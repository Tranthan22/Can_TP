from Common import I_PDU
 
data = """- Sometime in the early Cretaceous period of the Earth's history, hunting wasps of a certain type became bees by adopting a vegetarian diet: they began to rely more and more on the pollen of plants as a source of protein for themselves and their offspring, as an alternative to insects. In so doing, they accidentally transported pollen on their bodies to other plants of the same species, bringing about pollination. The stage was thus set for a succession of ever-closer mutual adaptations of bees and flowering plants. In particular, flowers began to reward bees for their unwitting role in their reproduction by providing richer sources of pollen and another source of nutrition, nectar.
- Today about 15 per cent of our diet consists of crops which are pollinated by bees. The meat and other animal products we consume are ultimately derived from bee- pollinated forage crops, and account for another 15 per cent. It follows that around one third of our food is directly or indirectly dependent on the pollinating services of bees. On a global basis, the annual value of agricultural crops dependent on the pollination services of bees is estimated at £1,000 million (US$1,590 million). Much of this pollination is due to honey bees, and in monetary terms it exceeds the value of the annual honey crop by a factor of fifty.
- But the apparently harmonious relationship between bees and plants conceals a conflict of interests. Although flowers need bees and vice versa, it pays each partner to minimise its costs and maximise its profits. This may sound like an extreme case of attributing human qualities to non-human species, but using the marketplace and the principles of double-entry book keeping as metaphors may give US some insights into what is really going on between bees and flowering plants. In the real world, both flower and bee operate in a competitive marketplace. A community of retailers, the flowers, seek to attract more or less discriminating consumers, the bees. Each flower has to juggle the costs and benefits of investing in advertising, by colour and scent, and providing rewards, nectar and pollen, clearly a species which depends on cross-pollination is on a knife-edge: it must provide sufficient nectar to attract the interest of a bee, but not enough to satisfy all of its needs in one visit. A satiated bee would return to its nest rather than visit another flower. The bee, on the other hand, is out to get the maximum amount of pollen and nectar. It must assess the quality and quantity of rewards which are on offer and juggle its energy costs so that it makes a calorific profit on each foraging trip. The apparent harmony between plants and bees is therefore not all that it seems. Instead, it is an equilibrium based on compromises between the competing interests of the protagonists."""
 
 
PDU_App_T = [
    I_PDU(ID = 0x11, SDU = data.encode('utf-8'), is_FD = True),
    I_PDU(ID = 0x22, SDU = "Hello".encode('utf-8'), is_FD = True),
    I_PDU(ID = 0x33, SDU = data.encode('utf-8'), is_FD = False),
    I_PDU(ID = 0x44, SDU = "PC here".encode('utf-8'), is_FD = False),
]
 
PDU_App_R = [
    I_PDU(ID = 0x55),
    I_PDU(ID = 0x66)
]