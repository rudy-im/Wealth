from Kiwoom import *
from KiwoomUtil import *
import time, sqlite3, threading
import sqlite3Util as sUtil

KUtil = None

interest40 = ['000020','000030','000050','000060','000070','000080',
            '000100','000120','000140','000150','000155','000180',
            '000210','000215','000220','000230','000240','000250',
            '000270','000320','000370','000390','000400','000430',
            '000480','000490','000500','000540','000640','000650',
            '000660','000670','000680','000700','000720','000810',
            '000815','000850','000860','000880','00088K','000890',
            '000910','000970','000990','001000','001040','001045',
            '001060','001080','001120','001130','001200','001230',
            '001250','001270','001340','001390','001420','001430',
            '001450','001460','001500','001510','001530','001540',
            '001550','001560','001620','001630','001680','001720',
            '001725','001740','001750','001770','001780','001790',
            '001810','001820','001840','001880','001940','002020',
            '002030','002100','002140','002150','002170','002200',
            '002210','002230','002240','002250','002270','002290',
            '002300','002310','002320','002350','002355','002360',
            '002380','002390','002450','002460','002550','002600',
            '002680','002690','002700','002720','002760','002790',
            '002795','002800','002810','002820','002880','002900',
            '002920','002960','002990','003000','003010','003030',
            '003070','003080','003090','003100','003120','003160',
            '003200','003220','003230','003240','003300','003310',
            '003350','003410','003460','003470','003490','003520',
            '003530','003540','003545','003550','003555','003560',
            '003570','003610','003620','003650','003670','003680',
            '003690','003780','003850','003920','003960','004000',
            '004020','004060','004090','004100','004130','004150',
            '004170','004250','004270','004310','004360','004370',
            '004380','004430','004440','004490','004540','004560',
            '004590','004650','004690','004700','004710','004720',
            '004770','004780','004800','004830','004840','004870',
            '004890','004910','004920','004960','004970','004980',
            '004990','005010','005090','005110','005160','005180',
            '005190','005250','005290','005300','005305','005320',
            '005360','005380','005385','005387','005389','005390',
            '005430','005440','005490','005500','005610','005670',
            '005680','005710','005720','005740','005750','005810',
            '005820','005830','005850','005860','005870','005880',
            '005930','005935','005940','005945','005950','005990',
            '006040','006050','006060','006090','006110','006120',
            '006125','006140','006220','006260','006280','006340',
            '006360','006370','006400','006405','006580','006650',
            '006660','006730','006800','006805','006840','006880',
            '006890','006910','006920','006980','007070','007160',
            '007210','007310','007340','007370','007460','007530',
            '007540','007570','007590','007610','007660','007690',
            '007700','007720','007770','007810','007820','007860',
            '008060','008250','008260','008290','008350','008370',
            '008420','008470','008490','008560','008600','008700',
            '008730','008770','008930','008970','009150','009155',
            '009160','009180','009200','009240','009270','009290',
            '009300','009320','009410','009420','009440','009450',
            '009460','009470','009520','009540','009580','009680',
            '009730','009770','009780','009830','009970','010040',
            '010050','010060','010100','010120','010130','010140',
            '010240','010420','010470','010620','010660','010690',
            '010770','010780','010820','010950','010955','010960',
            '011040','011070','011080','011090','011150','011170',
            '011210','011280','011320','011330','011370','011390',
            '011420','011500','011560','011690','011700','011760',
            '011780','011785','011790','011930','012160','012200',
            '012280','012320','012330','012450','012510','012610',
            '012620','012630','012690','012700','012750','012790',
            '012860','013000','013030','013120','013310','013520',
            '013570','013700','013720','013810','013870','013990',
            '014100','014130','014160','014190','014200','014280',
            '014440','014470','014530','014570','014580','014620',
            '014680','014710','014820','014830','014970','015230',
            '015260','015350','015360','015710','015750','015760',
            '015860','015890','016090','016100','016170','016250',
            '016360','016450','016580','016590','016600','016610',
            '016670','016710','016740','016800','017000','017040',
            '017180','017250','017370','017390','017480','017510',
            '017550','017650','017670','017800','017810','017890',
            '017940','017960','018120','018260','018310','018470',
            '018620','018670','018680','018880','019010','019170',
            '019210','019440','019540','019550','019680','019685',
            '019770','019990','020000','020120','020150','020180',
            '020560','020710','020760','021040','021080','021240',
            '021320','021650','021820','021960','022100','022220',
            '023000','023150','023160','023350','023410','023460',
            '023530','023590','023600','023760','023800','023810',
            '023890','023900','023910','024060','024090','024110',
            '024120','024660','024720','024740','024800','024840',
            '024880','024890','024900','024910','024950','025000',
            '025320','025440','025530','025540','025550','025620',
            '025750','025770','025820','025860','025870','025880',
            '025890','025900','025950','025980','026040','026150',
            '026890','026910','026940','026960','027050','027390',
            '027410','027580','027710','027830','028050','028080',
            '028100','028150','028260','02826K','028670','029460',
            '029530','029780','029960','030000','030190','030200',
            '030210','030520','030530','030610','030720','031310',
            '031330','031390','031430','031440','031510','031820',
            '031980','032080','032190','032280','032540','032560',
            '032580','032620','032640','032750','032830','032850',
            '032940','033100','033130','033160','033170','033180',
            '033240','033270','033290','033310','033320','033340',
            '033500','033530','033540','033560','033640','033660',
            '033780','033790','033830','033920','034020','034120',
            '034220','034230','034300','034310','034590','034730',
            '03473K','034810','034830','034940','034950','035000',
            '035080','035150','035200','035250','035420','035460',
            '035510','035600','035610','035620','035720','035760',
            '035810','035890','035900','036000','036010','036030',
            '036090','036170','036180','036190','036200','036420',
            '036460','036480','036490','036530','036560','036570',
            '036580','036640','036670','036690','036710','036800',
            '036810','036830','036890','036930','037070','037230',
            '037330','037350','037370','037440','037460','037560',
            '037710','037760','037950','038010','038060','038070',
            '038110','038160','038290','038390','038460','038500',
            '038540','038620','038680','038870','038880','038950',
            '039010','039030','039130','039240','039290','039310',
            '039340','039420','039440','039490','039570','039610',
            '039740','039830','039840','039980','040160','040300',
            '040420','040610','040910','041140','041190','041440',
            '041460','041510','041520','041650','041830','041910',
            '041920','041930','041960','042110','042370','042420',
            '042500','042510','042520','042600','042670','042700',
            '043150','043200','043260','043290','043340','043360',
            '043370','043610','043650','044060','044340','044450',
            '044490','044780','044820','044960','045060','045100',
            '045390','045510','045520','045660','046070','046110',
            '046120','046140','046390','046440','046890','046940',
            '046970','047040','047050','047310','047400','047810',
            '047820','047920','048260','048430','048470','048530',
            '048830','048910','049070','049080','049120','049430',
            '049470','049480','049520','049630','049720','049770',
            '049800','049830','049950','049960','050110','050120',
            '050760','050860','050960','051360','051390','051490',
            '051500','051600','051900','051905','051910','051915',
            '052220','052260','052300','052330','052400','052460',
            '052600','052670','052690','052710','052790','052900',
            '053030','053050','053160','053210','053260','053270',
            '053280','053290','053300','053350','053450','053610',
            '053620','053690','053700','053800','053950','053980',
            '054040','054050','054090','054180','054210','054220',
            '054450','054540','054620','054670','054780','054800',
            '054920','054940','054950','055550','056090','056190',
            '056360','056700','057030','057050','057540','058110',
            '058400','058430','058450','058470','058530','058610',
            '058630','058650','058730','058820','058850','058860',
            '059090','059100','059120','059210','060150','060240',
            '060250','060260','060370','060380','060480','060540',
            '060560','060570','060590','060720','060980','061040',
            '061250','061460','061970','063080','063160','063170',
            '063570','063760','064240','064260','064350','064480',
            '064520','064760','064800','064960','065060','065130',
            '065150','065350','065450','065510','065530','065570',
            '065660','065680','065690','065710','065950','066130',
            '066310','066410','066570','066575','066590','066620',
            '066670','066700','066900','066910','066970','066980',
            '067000','067010','067080','067160','067170','067280',
            '067290','067310','067390','067570','067730','067830',
            '067900','067920','068050','068240','068270','068290',
            '068330','068400','068760','068790','068930','068940',
            '069080','069110','069140','069260','069330','069410',
            '069500','069510','069540','069620','069640','069660',
            '069730','069960','070590','070960','071050','071055',
            '071090','071200','071280','071320','071460','071670',
            '071840','071850','072020','072130','072470','072710',
            '072770','072870','072950','072990','073070','073240',
            '073540','073560','074600','074610','075130','075180',
            '075580','075970','076080','076610','077360','077500',
            '078000','078020','078070','078130','078140','078150',
            '078160','078340','078350','078520','078590','078600',
            '078890','078930','078935','079000','079160','079170',
            '079190','079370','079430','079550','079650','079660',
            '079940','079950','079960','079970','079980','080010',
            '080160','080420','080470','080520','080580','081000',
            '081150','081580','081660','081970','082210','082640',
            '082660','083310','083420','083450','083470','083500',
            '083550','083640','083660','083930','084010','084110',
            '084180','084370','084650','084670','084680','084690',
            '084730','084870','084990','085370','08537M','085620',
            '085660','085670','085810','085910','086040','086060',
            '086280','086390','086450','086520','086670','086790',
            '086900','086960','086980','087260','087600','088130',
            '088350','088790','088800','088910','089030','089140',
            '089150','089470','089590','089600','089980','090080',
            '090150','090350','090360','090410','090430','090435',
            '090460','090470','090710','090730','090740','090850',
            '091120','091160','091170','091180','091210','091220',
            '091230','091340','091440','091580','091590','091700',
            '092040','092070','092130','092200','092220','092230',
            '092300','092440','092460','092600','092730','092870',
            '093050','093190','093240','093320','093370','093380',
            '093520','093920','094170','094280','094360','094480',
            '094840','094850','094940','094970','095190','095340',
            '095570','095610','095660','095720','095910','096240',
            '096530','096610','096630','096760','096770','096775',
            '097520','097870','097950','097955','098120','098460',
            '098560','099140','099190','099320','099440','100030',
            '100090','100120','100130','100220','100250','100660',
            '100700','100840','100910','101000','101060','101160',
            '101170','101240','101280','101330','101490','101530',
            '101670','101930','102110','102120','102210','102260',
            '102460','102710','102780','102940','102960','102970',
            '103140','103230','103590','104040','104200','104460',
            '104480','104520','104530','104540','104700','104830',
            '105010','105190','105330','105560','105630','105740',
            '105780','105840','106080','106190','106240','107590',
            '108230','108320','108380','108450','108590','108670',
            '108675','108790','109080','109610','109740','109860',
            '111110','111770','111820','111870','112040','112240',
            '112610','114090','114100','114190','114260','114450',
            '114460','114470','114570','114630','114800','114810',
            '114820','115160','115310','115390','115440','115480',
            '115500','115610','115960','117460','117580','117680',
            '117690','117700','119500','119610','119650','119830',
            '119850','119860','120030','120110','120115','120240',
            '121440','121600','121850','121890','122090','122260',
            '122350','122450','122640','122690','122870','122900',
            '122990','123010','123040','123100','123310','123330',
            '123410','123420','123570','123690','123700','123750',
            '123840','123860','123890','126560','126600','126640',
            '126700','126870','126880','127710','128940','129260',
            '130500','130580','130660','130680','130730','130740',
            '130960','131030','131090','131180','131220','131290',
            '131370','131390','131760','131890','131970','132030',
            '133690','133750','133820','134060','134380','134580',
            '134780','134790','136340','136480','136490','136510',
            '136540','137400','137610','137930','137940','137950',
            '138040','138070','138080','138230','138250','138360',
            '138490','138520','138530','138540','138910','138920',
            '138930','139050','139130','139220','139230','139240',
            '139250','139260','139270','139280','139290','139310',
            '139320','139480','139660','139670','140070','140410',
            '140520','140570','140580','140700','140710','140860',
            '140950','141000','141240','142210','142280','143160',
            '143210','143240','143460','143540','143850','143860',
            '144510','144600','144620','144960','145020','145210',
            '145670','145720','145850','145990','147760','147830',
            '147970','148020','148070','148250','149950','149980',
            '150460','151860','152100','152180','152280','152330',
            '152380','152870','153130','153270','153460','154040',
            '155650','155660','156080','156100','157450','157490',
            '157500','157510','157520','159800','160550','160580',
            '160600','160980','161000','161390','161490','161500',
            '161510','161570','161890','163560','166090','166400',
            '166480','167860','168300','168580','169950','170030',
            '170350','170900','170920','171120','173940','174350',
            '174360','174880','175140','175330','176440','176710',
            '176950','177350','177830','178320','178780','178920',
            '180400','180640','181480','181710','182360','182480',
            '182490','182690','183190','183300','183700','183710',
            '184230','185680','185750','187220','187270','187420',
            '189300','189400','189690','189860','189980','190150',
            '190160','190510','190620','191420','192080','192090',
            '192250','192390','192400','192410','192440','192530',
            '192720','192820','193250','194370','194480','194510',
            '194610','195440','195870','195920','195930','195970',
            '195980','195990','196170','196230','196300','196490',
            '196700','197210','198440','200020','200030','200040',
            '200050','200130','200230','200250','200470','200670',
            '200710','200780','200880','201490','203450','203650',
            '203690','203780','204320','204630','204840','204990',
            '205100','205720','206400','206560','206640','206650',
            '206660','207720','207760','207930','207940','208140',
            '208350','208370','208470','208640','208710','208860',
            '208870','210540','210780','210980','211210','211260',
            '211270','211560','211900','212560','213090','213420',
            '213500','213610','213630','214150','214180','214270',
            '214320','214330','214370','214390','214420','214430',
            '214450','214680','214980','215000','215090','215100',
            '215200','215360','215380','215480','215580','215600',
            '215620','215750','215790','216050','217190','217270',
            '217480','217500','217600','217620','217770','217780',
            '217790','217810','217820','218150','218410','218420',
            '218710','219130','219390','219480','219550','219580',
            '219860','219960','220130','220630','221200','221610',
            '221840','221950','221980','222040','222080','222170',
            '222180','222190','222200','222390','222420','222800',
            '222810','222980','223040','223190','223310','224110',
            '225030','225330','225430','225440','225530','225570',
            '225590','225650','225800','226320','226340','226350',
            '226360','226380','226440','226490','226810','226850',
            '226980','227540','227550','227560','227570','227830',
            '227840','227950','228340','228790','228800','228810',
            '228820','228850','229200','229640','229720','230240',
            '230360','230480','230490','230980','232080','232140',
            '232270','234080','234310','234920','235010','236200',
            '236460','237350','237370','237440','237690','237750',
            '237880','238090','238120','238670','238720','239340',
            '239610','239660','240540','240810','241180','241390',
            '241520','241560','241590','241690','241710','241790',
            '242040','243070','244580','244620','244660','244670',
            '244820','245340','245350','245360','245710','246690',
            '246720','247780','247790','247800','248170','248260',
            '248270','249420','250060','250730','250780','250930',
            '251340','251350','251370','251590','251600','251890',
            '252000','252410','252650','252720','252730','253150',
            '253240','253280','253290','253990','254120','256440',
            '256450','256630','256750','256840','257730','258790',
            '260200','260270','261060','261070','261110','261120',
            '261140','261220','261240','261250','261260','261270',
            '261920','262830','263190','263770','264290','264450',
            '264900','26490K','265520','265690','266140','266160',
            '266360','266370','266390','266410','266420','266550',
            '267300','267440','267450','267490','267500','267770',
            '900120','900140','900250','900260','900270','900280',
            '900290','900300','950110','950130','950140']

interest30 = ['000030', '000050', '000060', '000070', '000080', '000100', 
            '000120', '000150', '000210', '000240', '000250', '000270', 
            '000370', '000400', '000640', '000660', '000670', '000720', 
            '000810', '000815', '000880', '00088K', '000990', '001040', 
            '001060', '001120', '001130', '001200', '001430', '001450', 
            '001500', '001510', '001630', '001680', '001720', '001740', 
            '001780', '002020', '002240', '002250', '002270', '002320', 
            '002350', '002380', '002390', '002550', '002790', '002810', 
            '002960', '002990', '003000', '003030', '003090', '003220', 
            '003230', '003240', '003300', '003410', '003470', '003490', 
            '003520', '003540', '003550', '003620', '003670', '003690', 
            '003850', '003920', '004000', '004020', '004130', '004150', 
            '004170', '004370', '004430', '004490', '004690', '004710', 
            '004800', '004990', '005090', '005180', '005250', '005290', 
            '005300', '005380', '005385', '005387', '005440', '005490', 
            '005500', '005610', '005720', '005740', '005830', '005850', 
            '005880', '005930', '005935', '005940', '005990', '006040', 
            '006060', '006120', '006260', '006280', '006360', '006400', 
            '006650', '006730', '006800', '006840', '007070', '007160', 
            '007310', '007340', '007570', '007700', '007810', '007820', 
            '008060', '008490', '008560', '008730', '008770', '008930', 
            '009150', '009240', '009290', '009410', '009420', '009450', 
            '009540', '009830', '009970', '010050', '010060', '010120', 
            '010130', '010140', '010620', '010780', '010950', '011070', 
            '011170', '011210', '011780', '011790', '011930', '012330', 
            '012450', '012510', '012630', '012750', '013030', '013120', 
            '014620', '014680', '014820', '014830', '015750', '015760', 
            '016100', '016170', '016250', '016360', '016450', '016580', 
            '017390', '017670', '017800', '017810', '017940', '018260', 
            '018670', '018880', '019170', '019680', '020000', '020150', 
            '020560', '021240', '021960', '022100', '023410', '023530', 
            '023590', '024110', '024660', '024720', '025540', '025770', 
            '025860', '025900', '025980', '026960', '027410', '028050', 
            '028150', '028260', '028670', '029460', '029530', '029780', 
            '030000', '030190', '030200', '030520', '030530', '030610', 
            '031390', '031430', '031440', '031980', '032190', '032640', 
            '032830', '033270', '033290', '033780', '033920', '034020', 
            '034120', '034220', '034230', '034310', '034730', '034830', 
            '035080', '035250', '035420', '035600', '035720', '035760', 
            '035810', '036420', '036460', '036490', '036570', '036580', 
            '036830', '036930', '037560', '038540', '039030', '039130', 
            '039490', '039840', '041510', '041830', '041960', '042670', 
            '042700', '043150', '043370', '044490', '044820', '046890', 
            '047050', '047810', '048260', '049770', '049960', '051500', 
            '051600', '051900', '051905', '051910', '051915', '052690', 
            '053030', '053210', '053800', '055550', '056190', '057050', 
            '058470', '058650', '058820', '060980', '063080', '064350', 
            '064760', '064960', '066570', '066575', '066970', '067080', 
            '067290', '068240', '068270', '068760', '069080', '069260', 
            '069500', '069620', '069660', '069960', '071050', '071320', 
            '071840', '072710', '073240', '078150', '078160', '078340', 
            '078520', '078930', '079160', '079430', '079550', '080160', 
            '081660', '082640', '084110', '084370', '084690', '084990', 
            '085620', '085660', '086280', '086450', '086790', '086900', 
            '086980', '088350', '089590', '089600', '090430', '090435', 
            '090460', '091700', '092040', '093050', '093370', '095340', 
            '095570', '095610', '096530', '096760', '096770', '097950', 
            '098460', '099190', '100120', '100130', '101060', '101530', 
            '102110', '102780', '102940', '103140', '104700', '104830', 
            '105190', '105560', '105630', '108230', '108320', '108670', 
            '108790', '111770', '112040', '112610', '114090', '114100', 
            '114260', '114800', '115390', '115960', '120110', '122870', 
            '122900', '122990', '123100', '123890', '126560', '128940', 
            '130730', '130960', '136480', '136490', '138040', '138250', 
            '138930', '139130', '139480', '145020', '145720', '145990', 
            '148020', '152100', '152330', '152870', '153130', '157450', 
            '161000', '161390', '161890', '168580', '170900', '175330', 
            '178920', '180640', '181710', '185750', '192080', '192400', 
            '192440', '192530', '192820', '195870', '200130', '200880', 
            '204320', '206640', '207940', '210980', '213420', '213500', 
            '214320', '214370', '214390', '214420', '214450', '214980', 
            '215000', '215600', '222040', '226320', '228850', '237690', 
            '237880', '240810', '241560', '241590', '243070', '249420', 
            '900140']

# kiwoomRequest() 에서 데이터 조회가 완료될 때까지 기다리는 thread 전용
def waitDuringQuery(rqname):
    
    while True:
        
        time.sleep(0.2)
        

        #print("\n")
        #print("[waitDuringQuery()]")
            
        if kiwoom.isQueryFinished(rqname):
            
            #print("\n")
            #print("[waitDuringQuery()] Query is finished!!")
                
            break



            

def getNow(rettype='str'):
    localtime = time.localtime()
    now = localtime.tm_hour * 10000 + localtime.tm_min * 100 + localtime.tm_sec

    #print("[getNow()] now : " + str(now))

    if rettype == 'str':
        return str(now)
    else:
        return now
    




def saveRealData():

    i = 0
    codeCount = len(interest30)
    realtime = getNow()
   
    filename = 'realtime data/' + sUtil.now(False) + '.txt'
    fp = open(filename, 'a')
    
    while i<codeCount:

        end = i+100
        if end>codeCount: end = codeCount

        print("\n")
        print("query start")
        
        kiwoom.commKwRqData(';'.join(interest30[i:end]), 0, end-i, 0, 'rq', '0101', ['종목코드', '현재가', '거래량'])

        wait = threading.Thread(target=waitDuringQuery, args=['rq'])
        wait.start()
        wait.join()
        
        print("query end")

        df = kiwoom.getRqResult('rq')
        df.columns = ['code', 'price', 'volume']
        
        

        print("save start")
        
        KUtil.saveRealtimeData(fp, df, realtime)

        print("save end")

        i = end

    fp.close()

    
def recordRealtime():

    timeInterval = 0.2
    beforetime = getNow('int')
    nowtime = beforetime
    
    while True:
        #print('[recordRealtime()]')
        
        beforetime = nowtime
        nowtime = getNow('int')
        
        if nowtime<90000:
            pass
        
        elif nowtime>153000:
            break
        
        elif beforetime<nowtime:
            saveRealData()
            
        time.sleep(timeInterval)



def listarrange(l):
    str = ''
    for i in range(len(l)):
        str = str + "'" + l[i] + "', "
        if (i+1)%6==0:
            print(str)
            str = ''
    print(str)


# 1초마다 체크하는 thread 내용
def infoUpdate():
    beforetime = KUtil.getNow()
    nowtime = beforetime
    
    # True이면 자원 이용 중
    semaphore = False
    
    while True:
        if not(semaphore):
            nowtime = KUtil.getNow()
            
            if nowtime>beforetime:
                semaphore = True
                print(nowtime)

                filename = 'realtime data/' + sUtil.now(False) + '.txt'
                fp = open(filename, 'a')
                
                realpool = kiwoom.getRealpool().copy()

                if realpool!={}:
                    
                    df = DataFrame(columns = ['code', 'price', 'volume'])
                    i = 0
                    
                    for k, v in realpool.items():
                        df.loc[i] = [k, v[0], v[1]]
                        i += 1
                        
                    KUtil.saveRealtimeData(fp, df, nowtime)

                fp.close()
                beforetime = nowtime
                semaphore = False
        
        time.sleep(0.2)
        
        

            
if __name__ == "__main__":
    app = QApplication(sys.argv)
    kiwoom = Kiwoom()
    kiwoom.commConnect()
    KUtil = KiwoomUtil(kiwoom)
    KUtil.setRealtime(KUtil.queryByMargin(20))

    #saveRealData()

    th = threading.Thread(target = infoUpdate)
    th.start()
    #th.join()
    
